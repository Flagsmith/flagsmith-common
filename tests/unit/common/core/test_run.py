from unittest.mock import MagicMock

import pytest
from django.test import override_settings
from pytest_mock import MockerFixture

from common.core.cli import run


@pytest.fixture
def mock_run(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("common.core.cli.run.django_execute_from_command_line")


def test_serve__default__waits_for_db_then_starts_api(
    mock_run: MagicMock,
) -> None:
    # Given / When
    run.serve([], prog="flagsmith serve")

    # Then
    assert [call.args[0] for call in mock_run.call_args_list] == [
        ["flagsmith", "waitfordb", "--database", "default"],
        ["flagsmith", "start", "api"],
    ]


def test_serve__extra_args__forwarded_to_start(
    mock_run: MagicMock,
) -> None:
    # Given / When
    run.serve(["--workers", "5"], prog="flagsmith serve")

    # Then
    assert [call.args[0] for call in mock_run.call_args_list][-1] == [
        "flagsmith",
        "start",
        "api",
        "--workers",
        "5",
    ]


def test_serve__skip_wait_for_db_set__does_not_wait(
    mock_run: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("SKIP_WAIT_FOR_DB", "1")

    # When
    run.serve([], prog="flagsmith serve")

    # Then
    assert [call.args[0] for call in mock_run.call_args_list] == [
        ["flagsmith", "start", "api"]
    ]


def test_migrate__no_args__migrates_default_then_creates_cache_table(
    mock_run: MagicMock,
) -> None:
    # Given / When
    run.migrate([], prog="flagsmith migrate")

    # Then
    assert [call.args[0] for call in mock_run.call_args_list] == [
        ["flagsmith", "waitfordb", "--database", "default"],
        ["flagsmith", "migrate", "--database", "default"],
        ["flagsmith", "createcachetable"],
    ]


@override_settings(
    FLAGSMITH_MIGRATE_DATABASES=["default", "analytics", "task_processor"]
)
def test_migrate__configured_databases__migrates_each_in_order(
    mock_run: MagicMock,
) -> None:
    # Given / When
    run.migrate([], prog="flagsmith migrate")

    # Then
    assert [call.args[0] for call in mock_run.call_args_list] == [
        ["flagsmith", "waitfordb", "--database", "default"],
        ["flagsmith", "migrate", "--database", "default"],
        ["flagsmith", "migrate", "--database", "analytics"],
        ["flagsmith", "migrate", "--database", "task_processor"],
        ["flagsmith", "createcachetable"],
    ]


def test_migrate__with_args__defers_to_django_migrate(
    mock_run: MagicMock,
) -> None:
    # Given / When
    run.migrate(["myapp", "0042"], prog="flagsmith migrate")

    # Then — targeted migration only, no composite steps
    assert [call.args[0] for call in mock_run.call_args_list] == [
        ["flagsmith", "migrate", "myapp", "0042"],
    ]


def test_run_task_processor__default__migrates_waits_then_starts(
    mock_run: MagicMock,
) -> None:
    # Given / When
    run.run_task_processor([], prog="flagsmith run-task-processor")

    # Then — migrates (like run-docker.sh), waits for migrations, then starts
    assert [call.args[0] for call in mock_run.call_args_list] == [
        ["flagsmith", "waitfordb", "--database", "default"],
        ["flagsmith", "migrate", "--database", "default"],
        ["flagsmith", "createcachetable"],
        [
            "flagsmith",
            "waitfordb",
            "--database",
            "default",
            "--waitfor",
            "30",
            "--migrations",
        ],
        ["flagsmith", "start", "task-processor"],
    ]


@override_settings(
    FLAGSMITH_MIGRATE_DATABASES=["default", "analytics"],
    FLAGSMITH_WAIT_FOR_MIGRATIONS_DATABASES=["default", "analytics"],
)
def test_run_task_processor__configured_databases__migrates_and_waits_for_each(
    mock_run: MagicMock,
) -> None:
    # Given / When
    run.run_task_processor([], prog="flagsmith run-task-processor")

    # Then
    assert [call.args[0] for call in mock_run.call_args_list] == [
        ["flagsmith", "waitfordb", "--database", "default"],
        ["flagsmith", "migrate", "--database", "default"],
        ["flagsmith", "migrate", "--database", "analytics"],
        ["flagsmith", "createcachetable"],
        [
            "flagsmith",
            "waitfordb",
            "--database",
            "default",
            "--waitfor",
            "30",
            "--migrations",
        ],
        [
            "flagsmith",
            "waitfordb",
            "--database",
            "analytics",
            "--waitfor",
            "30",
            "--migrations",
        ],
        ["flagsmith", "start", "task-processor"],
    ]


def test_migrate_and_serve__no_startup_commands__migrates_then_serves(
    mock_run: MagicMock,
) -> None:
    # Given / When
    run.migrate_and_serve([], prog="flagsmith migrate-and-serve")

    # Then
    assert [call.args[0] for call in mock_run.call_args_list] == [
        ["flagsmith", "waitfordb", "--database", "default"],
        ["flagsmith", "migrate", "--database", "default"],
        ["flagsmith", "createcachetable"],
        ["flagsmith", "start", "api"],
    ]


@override_settings(FLAGSMITH_STARTUP_COMMANDS=["bootstrap"])
def test_migrate_and_serve__startup_commands__runs_them_between_migrate_and_serve(
    mock_run: MagicMock,
) -> None:
    # Given / When
    run.migrate_and_serve([], prog="flagsmith migrate-and-serve")

    # Then
    assert [call.args[0] for call in mock_run.call_args_list] == [
        ["flagsmith", "waitfordb", "--database", "default"],
        ["flagsmith", "migrate", "--database", "default"],
        ["flagsmith", "createcachetable"],
        ["flagsmith", "bootstrap"],
        ["flagsmith", "start", "api"],
    ]
