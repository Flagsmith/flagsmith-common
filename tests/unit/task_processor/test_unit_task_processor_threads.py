import logging
import typing

import pytest
from django.db import DatabaseError
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from task_processor import threads


@pytest.mark.parametrize(
    "exception, exception_repr",
    [
        (
            DatabaseError("Database error"),
            "django.db.utils.DatabaseError('Database error')",
        ),
        (
            Exception("Generic error"),
            "builtins.Exception('Generic error')",
        ),
    ],
)
@pytest.mark.django_db
def test_task_runner_is_resilient_to_errors(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    exception: Exception,
    exception_repr: str,
) -> None:
    # Given
    task_runner = threads.TaskRunner()
    mocker.patch.object(threads, "run_tasks", side_effect=exception)
    close_old_connections = mocker.patch.object(threads, "close_old_connections")

    # When
    task_runner.run_iteration()

    # Then
    logs = [(record.levelno, record.message) for record in caplog.records]
    assert logs == [
        (
            logging.ERROR,
            f"Error handling tasks from database 'default': {exception_repr}",
        ),
    ]
    close_old_connections.assert_called_once_with()


def test_task_runner__multi_database___consumes_tasks_from_multiple_databases(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.TASK_PROCESSOR_DATABASES = ["default", "task_processor"]
    run_tasks = mocker.patch.object(threads, "run_tasks")
    run_recurring_tasks = mocker.patch.object(threads, "run_recurring_tasks")
    task_runner = mocker.Mock()

    # When
    threads.TaskRunner.run_iteration(task_runner)

    # Then
    assert run_tasks.call_args_list == [
        mocker.call("default", task_runner.queue_pop_size),
        mocker.call("task_processor", task_runner.queue_pop_size),
    ]
    assert run_recurring_tasks.call_args_list == [
        mocker.call("task_processor"),
    ]


@pytest.mark.parametrize("database", ["default", "task_processor"])
def test_task_runner__single_database___consumes_tasks_from_one_databases(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    database: str,
) -> None:
    # Given
    settings.TASK_PROCESSOR_DATABASES = [database]
    run_tasks = mocker.patch.object(threads, "run_tasks")
    run_recurring_tasks = mocker.patch.object(threads, "run_recurring_tasks")
    task_runner = mocker.Mock()

    # When
    threads.TaskRunner.run_iteration(task_runner)

    # Then
    assert run_tasks.call_args_list == [
        mocker.call(database, task_runner.queue_pop_size),
    ]
    assert run_recurring_tasks.call_args_list == [
        mocker.call(database),
    ]


@pytest.mark.parametrize(
    "task_processor_databases",
    [
        ["default", "task_processor"],  # Default mode (try and consume remaining tasks)
        ["task_processor", "default"],  # Opt-out mode (try and consume remaining tasks)
        ["task_processor"],  # Single database mode
    ],
)
@pytest.mark.parametrize(
    "setup",
    [
        {  # Missing router and database
            "DATABASE_ROUTERS": [],
            "DATABASES": {"default": "exists but not task processor"},
        },
        {  # Missing database
            "DATABASE_ROUTERS": ["task_processor.routers.TaskProcessorRouter"],
            "DATABASES": {"default": "exists but not task processor"},
        },
        {  # Missing router
            "DATABASE_ROUTERS": [],
            "DATABASES": {
                "default": "hooray",
                "task_processor": "exists",
            },
        },
    ],
)
def test_validates_django_settings_are_compatible_with_multi_database_setup(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    setup: dict[str, typing.Any],
    task_processor_databases: list[str],
) -> None:
    # Given
    settings.TASK_PROCESSOR_DATABASES = task_processor_databases
    settings.DATABASE_ROUTERS = setup["DATABASE_ROUTERS"]
    settings.DATABASES = setup["DATABASES"]
    task_runner = mocker.Mock()

    # When
    with pytest.raises(AssertionError) as excinfo:
        threads.TaskRunner.run_iteration(task_runner)

    # Then
    assert str(excinfo.value) in [
        "DATABASE_ROUTERS must include 'task_processor.routers.TaskProcessorRouter' when using a separate task processor database.",
        "DATABASES must include 'task_processor' when using a separate task processor database.",
    ]
