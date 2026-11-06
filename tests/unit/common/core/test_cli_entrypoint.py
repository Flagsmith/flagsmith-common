import subprocess
import sys

import pytest
from pytest_mock import MockerFixture

from common.core.cli import entrypoint


@pytest.mark.parametrize(
    "subcommand", ["healthcheck", "checktaskprocessorthreadhealth"]
)
def test_main__healthcheck_subcommand__bypasses_full_cli(
    mocker: MockerFixture,
    subcommand: str,
) -> None:
    # Given
    mock_healthcheck = mocker.patch("common.core.cli.healthcheck.main")
    mock_full_main = mocker.patch("common.core.main.main")

    # When
    entrypoint.main(["/usr/bin/flagsmith", subcommand, "tcp", "--port", "8080"])

    # Then
    mock_healthcheck.assert_called_once_with(
        ["tcp", "--port", "8080"],
        prog=f"flagsmith {subcommand}",
    )
    mock_full_main.assert_not_called()


@pytest.mark.parametrize(
    "argv",
    [
        ["flagsmith"],
        ["flagsmith", "serve"],
        ["flagsmith", "showmigrations"],
    ],
)
def test_main__other_subcommand__delegates_to_full_cli(
    mocker: MockerFixture,
    argv: list[str],
) -> None:
    # Given
    mock_healthcheck = mocker.patch("common.core.cli.healthcheck.main")
    mock_full_main = mocker.patch("common.core.main.main")

    # When
    entrypoint.main(argv)

    # Then
    mock_full_main.assert_called_once_with(argv)
    mock_healthcheck.assert_not_called()


def test_main__healthcheck_tcp__does_not_import_heavy_modules() -> None:
    # Given
    # A fresh interpreter, so modules imported by the test session don't leak in
    script = (
        "import sys\n"
        "from common.core.cli.entrypoint import main\n"
        "try:\n"
        "    main(['flagsmith', 'healthcheck', 'tcp', '--port', '1'])\n"
        "except SystemExit:\n"
        "    pass\n"
        "heavy = ('django', 'environs', 'requests', 'sentry_sdk', 'structlog')\n"
        "print(sorted(m for m in heavy if m in sys.modules))\n"
    )

    # When
    output = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
    )

    # Then
    assert output.stdout.splitlines()[-1] == "[]"
