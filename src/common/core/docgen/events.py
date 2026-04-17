import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


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
    logger_domains = _collect_logger_domains(tree)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if entry := _build_entry_from_emit_call(node, logger_domains, path):
            yield entry


def _collect_logger_domains(tree: ast.AST) -> dict[str, str]:
    logger_domains: dict[str, str] = {}
    for node in ast.walk(tree):
        if not _is_logger_assignment(node):
            continue
        assert isinstance(node, ast.Assign)
        target = node.targets[0]
        assert isinstance(target, ast.Name)
        domain_arg = node.value.args[0]  # type: ignore[attr-defined]
        if isinstance(domain_arg, ast.Constant) and isinstance(domain_arg.value, str):
            logger_domains[target.id] = domain_arg.value
    return logger_domains


def _build_entry_from_emit_call(
    node: ast.Call,
    logger_domains: dict[str, str],
    path: Path,
) -> EventEntry | None:
    func = node.func
    if not isinstance(func, ast.Attribute):
        return None
    value = func.value
    if not isinstance(value, ast.Name) or value.id not in logger_domains:
        return None
    if not node.args:
        return None
    event_arg = node.args[0]
    if not (isinstance(event_arg, ast.Constant) and isinstance(event_arg.value, str)):
        return None
    return EventEntry(
        name=f"{logger_domains[value.id]}.{event_arg.value}",
        level=func.attr,
        attributes=frozenset(),
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
