import ast
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


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


def get_event_entries_from_source(
    source: str,
    *,
    module_dotted: str,
    path: Path,
) -> Iterator[EventEntry]:
    tree = ast.parse(source)
    logger_scopes = _collect_logger_scopes(tree, module_dotted=module_dotted, path=path)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if entry := _build_entry_from_emit_call(node, logger_scopes, path):
            yield entry


def _collect_logger_scopes(
    tree: ast.AST, *, module_dotted: str, path: Path
) -> dict[str, _LoggerScope]:
    logger_scopes: dict[str, _LoggerScope] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        target_id = node.targets[0].id
        if scope := _resolve_seed(
            node, logger_scopes=logger_scopes, module_dotted=module_dotted, path=path
        ):
            logger_scopes[target_id] = scope
        elif scope := _resolve_bind(node, logger_scopes=logger_scopes):
            logger_scopes[target_id] = scope
    return logger_scopes


def _resolve_seed(
    node: ast.Assign,
    *,
    logger_scopes: dict[str, _LoggerScope],
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
        return None
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
) -> EventEntry | None:
    func = node.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr not in EMIT_METHOD_NAMES:
        return None
    scope = _scope_for_emit_target(func.value, logger_scopes)
    if scope is None:
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
    return EventEntry(
        name=f"{scope.domain}.{event_arg.value}",
        level=func.attr,
        attributes=attributes,
        locations=[SourceLocation(path=path, line=node.lineno)],
    )


def _scope_for_emit_target(
    target: ast.expr,
    logger_scopes: dict[str, _LoggerScope],
) -> _LoggerScope | None:
    if isinstance(target, ast.Name):
        return logger_scopes.get(target.id)
    if isinstance(target, ast.Call):
        func = target.func
        if not isinstance(func, ast.Attribute) or func.attr != "bind":
            return None
        parent = _scope_for_emit_target(func.value, logger_scopes)
        if parent is None:
            return None
        return _LoggerScope(
            domain=parent.domain,
            bound_attrs=parent.bound_attrs | _kwargs_as_attributes(target.keywords),
        )
    return None


def _describe_emit_target(target: ast.expr) -> str:
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Call):
        func = target.func
        if isinstance(func, ast.Attribute):
            return f"{_describe_emit_target(func.value)}.{func.attr}(...)"
    return "<logger>"
