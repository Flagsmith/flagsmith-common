import ast
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator


class DocgenEventsWarning(UserWarning):
    """Raised by the events scanner when a call site can't be resolved."""


# Emission methods exposed by `structlog.stdlib.BoundLogger` whose first
# positional argument is the event name. `log` is excluded because its
# first argument is the level, not the event; `bind`/`unbind`/`new` are
# not emissions.
EMIT_METHOD_NAMES = frozenset(
    {
        "debug",
        "info",
        "warning",
        "warn",
        "error",
        "critical",
        "fatal",
        "exception",
        "msg",
    }
)


@dataclass(frozen=True)
class SourceLocation:
    path: Path
    line: int


@dataclass
class EventEntry:
    name: str
    level: str
    attributes: frozenset[str]
    locations: list[SourceLocation] = field(default_factory=list)


@dataclass(frozen=True)
class _LoggerScope:
    domain: str
    bound_attrs: frozenset[str]


_EXCLUDED_DIR_NAMES = frozenset({"migrations", "tests"})
_EXCLUDED_MANAGEMENT_DIR = ("management", "commands")
_TASK_PROCESSOR_APP_LABEL = "task_processor"


def get_event_entries_from_tree(
    root: Path,
    *,
    app_label: str,
    module_prefix: str,
) -> Iterator[EventEntry]:
    """Walk every `*.py` under `root` and yield its scanned event entries.

    Skips `migrations/`, `tests/`, `conftest.py`, and `test_*.py`. Also skips
    `management/commands/` unless `app_label == "task_processor"`, where the
    runner loop's events are operationally important.
    """
    for file_path in sorted(root.rglob("*.py")):
        if _should_skip(file_path.relative_to(root), app_label=app_label):
            continue
        rel_parts = file_path.relative_to(root).with_suffix("").parts
        module_dotted = ".".join((module_prefix, *rel_parts))
        yield from get_event_entries_from_source(
            file_path.read_text(),
            module_dotted=module_dotted,
            path=file_path,
        )


def _should_skip(relative: Path, *, app_label: str) -> bool:
    parts = relative.parts
    if any(part in _EXCLUDED_DIR_NAMES for part in parts[:-1]):
        return True
    filename = parts[-1]
    if filename == "conftest.py" or filename.startswith("test_"):
        return True
    if (
        len(parts) >= 3
        and parts[0] == _EXCLUDED_MANAGEMENT_DIR[0]
        and parts[1] == _EXCLUDED_MANAGEMENT_DIR[1]
        and app_label != _TASK_PROCESSOR_APP_LABEL
    ):
        return True
    return False


def merge_event_entries(entries: Iterable[EventEntry]) -> list[EventEntry]:
    """Collapse entries sharing an event name: union attributes and locations.

    Diverging log levels trigger a `DocgenEventsWarning`; the first-seen level
    wins. Output is sorted alphabetically by event name.
    """
    merged: dict[str, EventEntry] = {}
    for entry in entries:
        if existing := merged.get(entry.name):
            if entry.level != existing.level:
                original_location = existing.locations[0]
                new_location = entry.locations[0]
                warnings.warn(
                    f"`{entry.name}` is emitted at diverging log levels:"
                    f" `{existing.level}` at {original_location.path}:{original_location.line},"
                    f" `{entry.level}` at {new_location.path}:{new_location.line}."
                    f" Keeping first-seen level `{existing.level}`; reconcile"
                    " the emission sites to silence this warning.",
                    DocgenEventsWarning,
                    stacklevel=2,
                )
            existing.attributes = existing.attributes | entry.attributes
            existing_locations = set(existing.locations)
            for location in entry.locations:
                if location not in existing_locations:
                    existing.locations.append(location)
                    existing_locations.add(location)
        else:
            merged[entry.name] = EventEntry(
                name=entry.name,
                level=entry.level,
                attributes=entry.attributes,
                locations=list(entry.locations),
            )
    return sorted(merged.values(), key=lambda e: e.name)


def get_event_entries_from_source(
    source: str,
    *,
    module_dotted: str,
    path: Path,
) -> Iterator[EventEntry]:
    tree = ast.parse(source)
    visitor = _ScopeVisitor(module_dotted=module_dotted, path=path)
    visitor.visit(tree)
    yield from visitor.entries


class _ScopeVisitor(ast.NodeVisitor):
    """Walks the AST in source order with a stack of logger scopes.

    Entering a function body pushes a copy of the enclosing scope so
    binds that happen inside the function don't leak to sibling scopes.
    """

    def __init__(self, *, module_dotted: str, path: Path) -> None:
        self.module_dotted = module_dotted
        self.path = path
        self._scope_stack: list[dict[str, _LoggerScope]] = [{}]
        self._class_stack: list[dict[str, _LoggerScope]] = []
        self._module_classes: dict[str, dict[str, _LoggerScope]] = {}
        self.entries: list[EventEntry] = []

    @property
    def _scope(self) -> dict[str, _LoggerScope]:
        return self._scope_stack[-1]

    @property
    def _class_scope(self) -> dict[str, _LoggerScope] | None:
        return self._class_stack[-1] if self._class_stack else None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        class_scope: dict[str, _LoggerScope] = {}
        # Own methods take precedence — register them first.
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if accessor := _resolve_method_accessor(stmt, outer_scopes=self._scope):
                    class_scope[stmt.name] = accessor
        # Inherit from same-file parents declared earlier (Name-typed bases only).
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in self._module_classes:
                for method_name, method_scope in self._module_classes[base.id].items():
                    class_scope.setdefault(method_name, method_scope)
        self._module_classes[node.name] = class_scope
        self._class_stack.append(class_scope)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._scope_stack.append(dict(self._scope))
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._scope_stack.append(dict(self._scope))
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_id = node.targets[0].id
            if scope := _resolve_seed(
                node,
                module_dotted=self.module_dotted,
                path=self.path,
            ):
                self._scope[target_id] = scope
            elif scope := _resolve_bind(node, logger_scopes=self._scope):
                self._scope[target_id] = scope
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if entry := _build_entry_from_emit_call(
            node, self._scope, self.path, class_scope=self._class_scope
        ):
            self.entries.append(entry)
        self.generic_visit(node)


def _resolve_seed(
    node: ast.Assign,
    *,
    module_dotted: str,
    path: Path,
) -> _LoggerScope | None:
    call = node.value
    if not isinstance(call, ast.Call):
        return None
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr != "get_logger":
        return None
    if not isinstance(func.value, ast.Name) or func.value.id != "structlog":
        return None
    if not call.args:
        return _LoggerScope(domain="", bound_attrs=frozenset())
    target = node.targets[0]
    assert isinstance(target, ast.Name)
    domain = _resolve_domain(call.args[0], module_dotted=module_dotted)
    if domain is None:
        warnings.warn(
            f"{path}:{node.lineno}: cannot statically resolve logger domain"
            f" for `{target.id}`; skipping its events.",
            DocgenEventsWarning,
            stacklevel=2,
        )
        return None
    return _LoggerScope(domain=domain, bound_attrs=frozenset())


def _resolve_bind(
    node: ast.Assign,
    *,
    logger_scopes: dict[str, _LoggerScope],
) -> _LoggerScope | None:
    call = node.value
    if not isinstance(call, ast.Call):
        return None
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr != "bind":
        return None
    if not isinstance(func.value, ast.Name) or func.value.id not in logger_scopes:
        return None
    parent = logger_scopes[func.value.id]
    new_attrs = _kwargs_as_attributes(call.keywords)
    return _LoggerScope(
        domain=parent.domain,
        bound_attrs=parent.bound_attrs | new_attrs,
    )


def _resolve_domain(node: ast.expr, *, module_dotted: str) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and node.id == "__name__":
        return module_dotted
    return None


def _kwargs_as_attributes(keywords: list[ast.keyword]) -> frozenset[str]:
    return frozenset(kw.arg.replace("__", ".") for kw in keywords if kw.arg is not None)


def _build_entry_from_emit_call(
    node: ast.Call,
    logger_scopes: dict[str, _LoggerScope],
    path: Path,
    *,
    class_scope: dict[str, _LoggerScope] | None = None,
) -> EventEntry | None:
    func = node.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr not in EMIT_METHOD_NAMES:
        return None
    scope = _scope_for_emit_target(func.value, logger_scopes, class_scope=class_scope)
    if scope is None:
        if accessor_name := _self_cls_accessor_name(func.value):
            warnings.warn(
                f"{path}:{node.lineno}: cannot resolve"
                f" `{_describe_emit_target(func.value)}.{func.attr}(...)`:"
                f" `{accessor_name}` isn't a tracked accessor on this class"
                " or any same-file parent. Consider inlining the bind at the"
                " call site or moving the accessor into this file.",
                DocgenEventsWarning,
                stacklevel=2,
            )
        return None
    if not node.args:
        return None
    event_arg = node.args[0]
    if not (isinstance(event_arg, ast.Constant) and isinstance(event_arg.value, str)):
        warnings.warn(
            f"{path}:{node.lineno}: cannot statically resolve event name"
            f" for `{_describe_emit_target(func.value)}.{func.attr}(...)`;"
            " skipping. Consider annotating the call site with a"
            " `# docgen: event=<name>` comment so the catalogue can still"
            " pick it up.",
            DocgenEventsWarning,
            stacklevel=2,
        )
        return None
    attributes = scope.bound_attrs | _kwargs_as_attributes(node.keywords)
    name = f"{scope.domain}.{event_arg.value}" if scope.domain else event_arg.value
    return EventEntry(
        name=name,
        level=func.attr,
        attributes=attributes,
        locations=[SourceLocation(path=path, line=node.lineno)],
    )


def _scope_for_emit_target(
    target: ast.expr,
    logger_scopes: dict[str, _LoggerScope],
    *,
    class_scope: dict[str, _LoggerScope] | None = None,
) -> _LoggerScope | None:
    if isinstance(target, ast.Name):
        return logger_scopes.get(target.id)
    if isinstance(target, ast.Attribute):
        # `self.<name>` — method/property accessor on the enclosing class.
        if (
            class_scope is not None
            and isinstance(target.value, ast.Name)
            and target.value.id in _SELF_OR_CLS
            and target.attr in class_scope
        ):
            return class_scope[target.attr]
        return None
    if isinstance(target, ast.Call):
        func = target.func
        if not isinstance(func, ast.Attribute):
            return None
        # `self.<name>(...)` — method accessor invocation.
        if (
            class_scope is not None
            and isinstance(func.value, ast.Name)
            and func.value.id in _SELF_OR_CLS
            and func.attr in class_scope
        ):
            return class_scope[func.attr]
        if func.attr != "bind":
            return None
        parent = _scope_for_emit_target(
            func.value, logger_scopes, class_scope=class_scope
        )
        if parent is None:
            return None
        return _LoggerScope(
            domain=parent.domain,
            bound_attrs=parent.bound_attrs | _kwargs_as_attributes(target.keywords),
        )
    return None


_SELF_OR_CLS = frozenset({"self", "cls"})


def _self_cls_accessor_name(target: ast.expr) -> str | None:
    """Name of the accessor in a `self.<X>` / `cls.<X>(...)` emit shape, else None."""
    if isinstance(target, ast.Attribute):
        if isinstance(target.value, ast.Name) and target.value.id in _SELF_OR_CLS:
            return target.attr
    if isinstance(target, ast.Call):
        func = target.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id in _SELF_OR_CLS:
                return func.attr
    return None


def _resolve_method_accessor(
    func_def: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    outer_scopes: dict[str, _LoggerScope],
) -> _LoggerScope | None:
    """Return a scope for a method that just returns a bound logger."""
    body = list(func_def.body)
    # Allow a leading docstring.
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    if len(body) != 1:
        return None
    stmt = body[0]
    if not isinstance(stmt, ast.Return) or stmt.value is None:
        return None
    return _scope_for_emit_target(stmt.value, outer_scopes)


def _describe_emit_target(target: ast.expr) -> str:
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return f"{_describe_emit_target(target.value)}.{target.attr}"
    assert isinstance(target, ast.Call)
    func = target.func
    assert isinstance(func, ast.Attribute)
    return f"{_describe_emit_target(func.value)}.{func.attr}(...)"
