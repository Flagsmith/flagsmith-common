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
import io
import re
import sys
import tokenize
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


class Comment(NamedTuple):
    col: int
    text: str


def _extract_comments(source: str) -> dict[int, Comment]:
    """Return a mapping of line number (1-based) -> comment."""
    return {
        token.start[0]: Comment(col=token.start[1] + 1, text=token.string)
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.COMMENT
    }


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


_GWT_KEYWORDS = ("Given", "When", "Then")
_GWT_COMMENTS = frozenset(
    {
        "# Given",
        "# When",
        "# Then",
        "# Given / When",
        "# When / Then",
        "# Given / When / Then",
    }
)
_GWT_PREFIX_RE = re.compile(r"^(given|when|then)\b", re.IGNORECASE)


def _split_gwt_parts(comment: str) -> list[str] | None:
    """Split a GWT marker comment into slash-separated parts; None for other comments."""
    content = comment.lstrip("#").strip()
    if not _GWT_PREFIX_RE.match(content):
        return None
    return [part.strip() for part in content.split("/")]


def _find_missing_gwt(func_comments: list[str]) -> list[str]:
    """Return the Given/When/Then keywords absent from comments."""
    parts = {part for text in func_comments for part in _split_gwt_parts(text) or []}
    return [keyword for keyword in _GWT_KEYWORDS if keyword not in parts]


def check_ft004(
    tree: ast.Module, filepath: str, comments: dict[int, Comment]
) -> list[Violation]:
    """FT004: Missing or malformed # Given / # When / # Then comments in test body."""
    violations = []
    for node in ast.iter_child_nodes(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name.startswith("test_")
            and not _has_fixture_decorator(node)
        ):
            func_comments = {
                line_no: comment
                for line_no, comment in comments.items()
                if node.lineno <= line_no <= (node.end_lineno or node.lineno)
            }
            missing = _find_missing_gwt(
                [comment.text for comment in func_comments.values()]
            )
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
            for line_no, comment in func_comments.items():
                if _split_gwt_parts(comment.text) is None:
                    continue
                if comment.text in _GWT_COMMENTS:
                    continue
                violations.append(
                    Violation(
                        file=filepath,
                        line=line_no,
                        col=comment.col,
                        code="FT004",
                        message=(
                            f"GWT comment `{comment.text}` must be one of: "
                            + ", ".join(f"`{c}`" for c in sorted(_GWT_COMMENTS))
                        ),
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
        if v.line not in comments
        or not _is_noqa_suppressed(comments[v.line].text, v.code)
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
