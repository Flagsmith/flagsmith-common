import textwrap
from collections.abc import Callable
from pathlib import Path
from unittest.mock import ANY

import pytest

from common.lint_tests import Violation, lint_file, main

WriteTestFileFixture = Callable[..., str]


@pytest.fixture()
def write_test_file(tmp_path: Path) -> WriteTestFileFixture:
    """Write source to a test_*.py file and return its path."""

    def _write(source: str, filename: str = "test_example.py") -> str:
        p = tmp_path / filename
        p.write_text(textwrap.dedent(source))
        return str(p)

    return _write


@pytest.mark.parametrize(
    "source, expected_violations",
    [
        pytest.param(
            """\
            class TestFoo:
                pass
            """,
            [
                Violation(
                    file=ANY,
                    line=1,
                    col=1,
                    code="FT001",
                    message="Module-level test class `TestFoo` detected; use function-based tests",
                ),
            ],
            id="FT001-class-at-module-level",
        ),
        pytest.param(
            """\
            def test_something__with_nested__works():
                # Given
                class TestStub:
                    pass

                # When
                result = TestStub()

                # Then
                assert result is not None
            """,
            [],
            id="FT001-class-nested-in-function-ok",
        ),
        pytest.param(
            """\
            class MyHelper:
                pass
            """,
            [],
            id="FT001-non-test-class-ok",
        ),
        pytest.param(
            """\
            import unittest
            """,
            [
                Violation(
                    file=ANY,
                    line=1,
                    col=1,
                    code="FT002",
                    message="`import unittest` is not allowed; use pytest instead",
                ),
            ],
            id="FT002-import-unittest",
        ),
        pytest.param(
            """\
            from unittest import TestCase
            """,
            [
                Violation(
                    file=ANY,
                    line=1,
                    col=1,
                    code="FT002",
                    message="`from unittest import TestCase` is not allowed; use pytest instead",
                ),
            ],
            id="FT002-from-unittest-import-TestCase",
        ),
        pytest.param(
            """\
            from unittest.mock import MagicMock
            """,
            [],
            id="FT002-unittest-mock-ok",
        ),
        pytest.param(
            """\
            import unittest.mock
            """,
            [],
            id="FT002-import-unittest-mock-ok",
        ),
        pytest.param(
            """\
            def test_subject__condition__expected():
                # Given / When
                result = 1 + 1
                # Then
                assert result == 2
            """,
            [],
            id="FT003-correct-name-ok",
        ),
        pytest.param(
            """\
            def test_something():
                # Given / When
                result = 1 + 1
                # Then
                assert result == 2
            """,
            [
                Violation(
                    file=ANY,
                    line=1,
                    col=1,
                    code="FT003",
                    message="Test name `test_something` doesn't match `test_{subject}__{condition}__{expected}` (found 1 parts, expected 3)",
                ),
            ],
            id="FT003-missing-separators",
        ),
        pytest.param(
            """\
            import pytest

            @pytest.fixture
            def test_data():
                return 42
            """,
            [],
            id="FT003-FT004-fixture-skipped",
        ),
        pytest.param(
            """\
            import pytest

            @pytest.fixture()
            def test_data():
                return 42
            """,
            [],
            id="FT003-FT004-fixture-with-call-skipped",
        ),
        pytest.param(
            """\
            from pytest import fixture

            @fixture
            def test_data():
                return 42
            """,
            [],
            id="FT003-FT004-bare-fixture-skipped",
        ),
        pytest.param(
            """\
            from pytest import fixture

            @fixture()
            def test_data():
                return 42
            """,
            [],
            id="FT003-FT004-bare-fixture-call-skipped",
        ),
        pytest.param(
            """\
            def test_subject__condition__expected():
                # Given
                x = 1

                # When
                result = x + 1

                # Then
                assert result == 2
            """,
            [],
            id="FT004-all-gwt-present-ok",
        ),
        pytest.param(
            """\
            def test_subject__condition__expected():
                # Given
                x = 1

                # Then
                assert x == 1
            """,
            [
                Violation(
                    file=ANY,
                    line=1,
                    col=1,
                    code="FT004",
                    message="Test `test_subject__condition__expected` is missing GWT comments: When",
                ),
            ],
            id="FT004-missing-when",
        ),
        pytest.param(
            """\
            def test_subject__condition__expected():
                # Given / When
                result = 1 + 1

                # Then
                assert result == 2
            """,
            [],
            id="FT004-combined-given-when-ok",
        ),
        pytest.param(
            """\
            def test_subject__condition__expected():
                # Given
                x = 1

                # When / Then
                assert x == 1
            """,
            [],
            id="FT004-combined-when-then-ok",
        ),
        pytest.param(
            """\
            def test_something():  # a regular comment, not noqa
                pass
            """,
            [
                Violation(
                    file=ANY,
                    line=1,
                    col=1,
                    code="FT003",
                    message="Test name `test_something` doesn't match `test_{subject}__{condition}__{expected}` (found 1 parts, expected 3)",
                ),
                Violation(
                    file=ANY,
                    line=1,
                    col=1,
                    code="FT004",
                    message="Test `test_something` is missing GWT comments: Given, When, Then",
                ),
            ],
            id="regular-comment-does-not-suppress",
        ),
        pytest.param(
            """\
            class TestFoo:  # noqa
                pass
            """,
            [],
            id="noqa-bare-suppresses-all",
        ),
        pytest.param(
            """\
            def test_bad_name():  # noqa: FT003, FT004
                pass
            """,
            [],
            id="noqa-specific-codes-suppressed",
        ),
        pytest.param(
            """\
            def test_bad_name():  # noqa: FT001
                pass
            """,
            [
                Violation(
                    file=ANY,
                    line=1,
                    col=1,
                    code="FT003",
                    message="Test name `test_bad_name` doesn't match `test_{subject}__{condition}__{expected}` (found 1 parts, expected 3)",
                ),
                Violation(
                    file=ANY,
                    line=1,
                    col=1,
                    code="FT004",
                    message="Test `test_bad_name` is missing GWT comments: Given, When, Then",
                ),
            ],
            id="noqa-wrong-code-not-suppressed",
        ),
        pytest.param(
            """\
            import unittest  # noqa: FT002
            """,
            [],
            id="noqa-import-suppressed",
        ),
        pytest.param(
            "def broken(:\n",
            [
                Violation(
                    file=ANY,
                    line=1,
                    col=1,
                    code="FT000",
                    message="Could not parse file (SyntaxError)",
                ),
            ],
            id="FT000-syntax-error",
        ),
    ],
)
def test_lint_file__given_source__returns_expected_violations(
    write_test_file: WriteTestFileFixture,
    source: str,
    expected_violations: list[Violation],
) -> None:
    # Given
    path = write_test_file(source)

    # When
    violations = lint_file(path)

    # Then
    assert violations == expected_violations


@pytest.mark.parametrize(
    "filename",
    [
        pytest.param("conftest.py", id="conftest"),
        pytest.param("helpers.py", id="non-test-file"),
    ],
)
def test_lint_file__non_test_file__skipped(
    write_test_file: WriteTestFileFixture,
    filename: str,
) -> None:
    # Given
    path = write_test_file("class TestFoo: pass", filename=filename)

    # When
    violations = lint_file(path)

    # Then
    assert violations == []


def test_cli__error__exits_one(write_test_file: WriteTestFileFixture) -> None:
    # Given
    path = write_test_file(
        """\
        import unittest
        """
    )

    # When
    exit_code = main([path])

    # Then
    assert exit_code == 1
