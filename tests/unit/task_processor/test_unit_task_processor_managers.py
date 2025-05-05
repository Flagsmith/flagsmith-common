from collections.abc import Callable
from datetime import timedelta
from typing import Generator

import pytest
from django.db.utils import ProgrammingError
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from task_processor import managers
from task_processor.models import Task

now = timezone.now()
one_hour_ago = now - timedelta(hours=1)

pytestmark = pytest.mark.django_db


@pytest.fixture
def task_processor_database_tasks(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> Generator[Callable[..., list[Task]], None, None]:
    """
    Prepare a fake tasks processor database
    """

    def patch(*tasks: Task) -> list[Task]:
        def new_fetch_tasks(
            self: managers.TaskManager,
            database: str,
            num_tasks: int,
        ) -> Generator[Task, None, None]:
            if database == "task_processor":
                yield from tasks
                return
            yield from orig_fetch_tasks(self, database, num_tasks)

        orig_fetch_tasks = managers.TaskManager._fetch_tasks_from
        mocker.patch.object(
            managers.TaskManager, "_fetch_tasks_from", new=new_fetch_tasks
        )
        return list(tasks)

    mocker.patch.object(managers, "transaction")
    settings.DATABASES["task_processor"] = {"not": "undefined"}
    yield patch
    del settings.DATABASES["task_processor"]


@pytest.fixture
def missing_database_function(
    mocker: MockerFixture,
) -> Generator[Callable[..., list[Task]], None, None]:
    """
    Pretends the `get_tasks_to_process` database function does not exist
    """

    def patch(target_database: str, exception: Exception) -> None:
        class BrokenIterator:
            def __next__(self):
                raise exception

        def new_fetch_tasks(
            self: managers.TaskManager,
            database: str,
            num_tasks: int,
        ) -> Generator[Task, None, None]:
            if target_database == database:
                yield from BrokenIterator()
            yield from orig_fetch_tasks(self, database, num_tasks)

        orig_fetch_tasks = managers.TaskManager._fetch_tasks_from
        mocker.patch.object(
            managers.TaskManager, "_fetch_tasks_from", new=new_fetch_tasks
        )

    return patch


def test_TaskManager__default_database__consumes_tasks_from_database(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.object(managers.TaskManager, "_is_database_separate", new=False)
    new_tasks = [
        Task(task_identifier="some.identifier", scheduled_for=one_hour_ago),
        Task(task_identifier="some.identifier", scheduled_for=one_hour_ago),
    ]
    Task.objects.bulk_create(new_tasks)

    # When
    tasks = Task.objects.get_tasks_to_process(1)

    # Then
    assert list(tasks) == new_tasks[:1]


def test_TaskManager__default_database__task_processor_database_with_pending_tasks__consumes_tasks_from_old_database_first(
    mocker: MockerFixture,
    task_processor_database_tasks: Callable[..., list[Task]],
) -> None:
    # Given
    mocker.patch.object(managers.TaskManager, "_is_database_separate", new=False)
    old_tasks = task_processor_database_tasks(
        Task(task_identifier="some.identifier", scheduled_for=one_hour_ago),
        Task(task_identifier="some.identifier", scheduled_for=one_hour_ago),
    )
    new_tasks = [
        Task(task_identifier="some.identifier", scheduled_for=one_hour_ago),
        Task(task_identifier="some.identifier", scheduled_for=one_hour_ago),
    ]
    Task.objects.bulk_create(new_tasks)

    # When
    tasks = Task.objects.get_tasks_to_process(3)

    # Then
    assert list(tasks) == old_tasks + new_tasks[:1]


def test_TaskManager__default_database__task_processor_database_with_no_pending_tasks__consumes_tasks_from_new_database(
    mocker: MockerFixture,
    task_processor_database_tasks: Callable[..., list[Task]],
) -> None:
    # Given
    mocker.patch.object(managers.TaskManager, "_is_database_separate", new=False)
    task_processor_database_tasks()  # None
    new_tasks = [
        Task(task_identifier="some.identifier", scheduled_for=one_hour_ago),
        Task(task_identifier="some.identifier", scheduled_for=one_hour_ago),
    ]
    Task.objects.bulk_create(new_tasks)

    # When
    tasks = Task.objects.get_tasks_to_process(3)

    # Then
    assert list(tasks) == new_tasks


def test_TaskManager__default_database__task_processor_database_missing_function__consumes_tasks_from_default_database(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.object(managers.TaskManager, "_is_database_separate", new=False)
    raise


def test_TaskManager__task_processor_database__default_database_with_pending_tasks__consumes_tasks_from_old_database_first(
    mocker: MockerFixture,
) -> None:
    raise


def test_TaskManager__task_processor_database__default_database_with_no_pending_tasks__consumes_tasks_from_new_database(
    mocker: MockerFixture,
) -> None:
    raise


def test_TaskManager__task_processor_database__default_database_unaware_of_tasks__consumes_tasks_from_new_database(
    mocker: MockerFixture,
) -> None:
    raise
