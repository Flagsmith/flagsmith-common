"""Linter for Flagsmith test conventions.

Enforces:
- FT001: No module-level class Test* (function-only tests)
- FT002: No `import unittest` / `from unittest import TestCase` (unittest.mock is fine)
- FT003: Test name must have exactly 2 `__` separators: test_{subject}__{condition}__{expected}
- FT004: Test body must contain # Given, # When, and # Then comments

Output format matches ruff/flake8/mypy: {file}:{line}:{col}: {code} {message}
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import NamedTuple

UNITTEST_BANNED_IMPORTS = frozenset(
    {"TestCase", "TestSuite", "TestLoader", "TextTestRunner"}
)


class Violation(NamedTuple):
    file: str
    line: int
    col: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.col}: {self.code} {self.message}"


def _has_fixture_decorator(node: ast.FunctionDef) -> bool:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Attribute) and decorator.attr == "fixture":
            return True
        if isinstance(decorator, ast.Name) and decorator.id == "fixture":
            return True
        # Handle @pytest.fixture(...)
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "fixture"
        ):
            return True
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func.id == "fixture"
        ):
            return True
    return False


_COMMENT_RE = re.compile(r"#(.*)$")


def _extract_comments(source: str) -> dict[int, str]:
    """Return a mapping of line number (1-based) -> comment text."""
    comments: dict[int, str] = {}
    for lineno, line in enumerate(source.splitlines(), start=1):
        match = _COMMENT_RE.search(line)
        if match:
            comments[lineno] = "#" + match.group(1)
    return comments


_NOQA_RE = re.compile(r"#\s*noqa\b(?::\s*(?P<codes>[A-Z0-9,\s]+))?")


def _is_noqa_suppressed(comment: str, code: str) -> bool:
    """Check if a comment contains a noqa directive that suppresses the given code."""
    match = _NOQA_RE.search(comment)
    if not match:
        return False
    codes_str = match.group("codes")
    # Bare noqa (without specific codes) suppresses everything
    if codes_str is None:
        return True
    codes = {c.strip() for c in codes_str.split(",")}
    return code in codes


def check_ft001(tree: ast.Module, filepath: str) -> list[Violation]:
    """FT001: Module-level class Test* detected."""
    violations = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            violations.append(
                Violation(
                    file=filepath,
                    line=node.lineno,
                    col=node.col_offset + 1,
                    code="FT001",
                    message=f"Module-level test class `{node.name}` detected; use function-based tests",
                )
            )
    return violations


def check_ft002(tree: ast.Module, filepath: str) -> list[Violation]:
    """FT002: import unittest / from unittest import TestCase etc. (NOT unittest.mock)."""
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Flag `import unittest` but not `import unittest.mock`
                if alias.name == "unittest":
                    violations.append(
                        Violation(
                            file=filepath,
                            line=node.lineno,
                            col=node.col_offset + 1,
                            code="FT002",
                            message="`import unittest` is not allowed; use pytest instead",
                        )
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module == "unittest":
                for alias in node.names:
                    if alias.name in UNITTEST_BANNED_IMPORTS:
                        violations.append(
                            Violation(
                                file=filepath,
                                line=node.lineno,
                                col=node.col_offset + 1,
                                code="FT002",
                                message=f"`from unittest import {alias.name}` is not allowed; use pytest instead",
                            )
                        )
    return violations


def check_ft003(tree: ast.Module, filepath: str) -> list[Violation]:
    """FT003: Test name doesn't follow test_{subject}__{condition}__{expected} convention."""
    violations = []
    for node in ast.iter_child_nodes(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name.startswith("test_")
            and not _has_fixture_decorator(node)
        ):
            # Strip `test_` prefix and count `__` separators
            after_prefix = node.name[5:]
            parts = after_prefix.split("__")
            if len(parts) != 3:
                violations.append(
                    Violation(
                        file=filepath,
                        line=node.lineno,
                        col=node.col_offset + 1,
                        code="FT003",
                        message=f"Test name `{node.name}` doesn't match `test_{{subject}}__{{condition}}__{{expected}}` (found {len(parts)} parts, expected 3)",
                    )
                )
    return violations


def _find_missing_gwt(func_comments: list[str]) -> list[str]:
    """Return list of missing Given/When/Then keywords from comments."""
    has_given = False
    has_when = False
    has_then = False
    for text in func_comments:
        normalized = text.lstrip("#").strip().lower()
        if normalized.startswith("given"):
            has_given = True
            # "Given / When" satisfies both
            if "when" in normalized:
                has_when = True
        if normalized.startswith("when"):
            has_when = True
            # "When / Then" satisfies both
            if "then" in normalized:
                has_then = True
        if normalized.startswith("then"):
            has_then = True

    missing = []
    if not has_given:
        missing.append("Given")
    if not has_when:
        missing.append("When")
    if not has_then:
        missing.append("Then")
    return missing


def check_ft004(
    tree: ast.Module, filepath: str, comments: dict[int, str]
) -> list[Violation]:
    """FT004: Missing # Given, # When, or # Then comments in test body."""
    violations = []
    for node in ast.iter_child_nodes(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name.startswith("test_")
            and not _has_fixture_decorator(node)
        ):
            func_comments = [
                text
                for line_no, text in comments.items()
                if node.lineno <= line_no <= (node.end_lineno or node.lineno)
            ]
            missing = _find_missing_gwt(func_comments)
            if missing:
                violations.append(
                    Violation(
                        file=filepath,
                        line=node.lineno,
                        col=node.col_offset + 1,
                        code="FT004",
                        message=f"Test `{node.name}` is missing GWT comments: {', '.join(missing)}",
                    )
                )
    return violations


def lint_file(filepath: str) -> list[Violation]:
    """Run all checks on a single file."""
    path = Path(filepath)

    # Only check test_*.py files
    if not (path.name.startswith("test_") and path.suffix == ".py"):
        return []

    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return [
            Violation(
                file=filepath,
                line=1,
                col=1,
                code="FT000",
                message="Could not parse file (SyntaxError)",
            )
        ]

    comments = _extract_comments(source)

    violations = []
    violations.extend(check_ft001(tree, filepath))
    violations.extend(check_ft002(tree, filepath))
    violations.extend(check_ft003(tree, filepath))
    violations.extend(check_ft004(tree, filepath, comments))

    # Filter out violations suppressed by noqa comments
    return [
        v
        for v in violations
        if v.line not in comments or not _is_noqa_suppressed(comments[v.line], v.code)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint Flagsmith test conventions",
    )
    parser.add_argument("files", nargs="*", help="Files to check")
    args = parser.parse_args(argv)

    has_errors = False
    for filepath in args.files:
        violations = lint_file(filepath)
        for v in violations:
            has_errors = True
            print(v)

    return 1 if has_errors else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
