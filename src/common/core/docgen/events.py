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


def get_event_entries_from_source(
    source: str,
    *,
    module_dotted: str,
    path: Path,
) -> Iterator[EventEntry]:
    tree = ast.parse(source)
    logger_domains = _collect_logger_domains(
        tree, module_dotted=module_dotted, path=path
    )

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if entry := _build_entry_from_emit_call(node, logger_domains, path):
            yield entry


def _collect_logger_domains(
    tree: ast.AST, *, module_dotted: str, path: Path
) -> dict[str, str]:
    logger_domains: dict[str, str] = {}
    for node in ast.walk(tree):
        if not _is_logger_assignment(node):
            continue
        assert isinstance(node, ast.Assign)
        target = node.targets[0]
        assert isinstance(target, ast.Name)
        domain_arg = node.value.args[0]  # type: ignore[attr-defined]
        domain = _resolve_domain(domain_arg, module_dotted=module_dotted)
        if domain is None:
            warnings.warn(
                f"{path}:{node.lineno}: cannot statically resolve logger domain"
                f" for `{target.id}`; skipping its events.",
                DocgenEventsWarning,
                stacklevel=2,
            )
            continue
        logger_domains[target.id] = domain
    return logger_domains


def _resolve_domain(node: ast.expr, *, module_dotted: str) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and node.id == "__name__":
        return module_dotted
    return None


def _build_entry_from_emit_call(
    node: ast.Call,
    logger_domains: dict[str, str],
    path: Path,
) -> EventEntry | None:
    func = node.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr not in EMIT_METHOD_NAMES:
        return None
    value = func.value
    if not isinstance(value, ast.Name) or value.id not in logger_domains:
        return None
    if not node.args:
        return None
    event_arg = node.args[0]
    if not (isinstance(event_arg, ast.Constant) and isinstance(event_arg.value, str)):
        warnings.warn(
            f"{path}:{node.lineno}: cannot statically resolve event name"
            f" for `{value.id}.{func.attr}(...)`; skipping."
            " Consider annotating the call site with a `# docgen: event=<name>`"
            " comment so the catalogue can still pick it up.",
            DocgenEventsWarning,
            stacklevel=2,
        )
        return None
    attributes = frozenset(
        kw.arg.replace("__", ".") for kw in node.keywords if kw.arg is not None
    )
    return EventEntry(
        name=f"{logger_domains[value.id]}.{event_arg.value}",
        level=func.attr,
        attributes=attributes,
        locations=[SourceLocation(path=path, line=node.lineno)],
    )


def _is_logger_assignment(node: ast.AST) -> bool:
    if not isinstance(node, ast.Assign):
        return False
    if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
        return False
    call = node.value
    if not isinstance(call, ast.Call):
        return False
    func = call.func
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr != "get_logger":
        return False
    if not isinstance(func.value, ast.Name) or func.value.id != "structlog":
        return False
    return bool(call.args)
