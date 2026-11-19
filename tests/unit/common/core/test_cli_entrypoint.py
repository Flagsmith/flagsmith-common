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
