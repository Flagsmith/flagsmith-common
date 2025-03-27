import logging
import time
import typing
import uuid
from datetime import timedelta
from threading import Thread

import pytest
from django.core.cache import cache
from django.utils import timezone
from freezegun import freeze_time
from pytest import MonkeyPatch
from pytest_mock import MockerFixture

from common.test_tools import AssertMetricFixture
from task_processor.decorators import (
    TaskHandler,
    register_recurring_task,
    register_task_handler,
)
from task_processor.models import (
    RecurringTask,
    RecurringTaskRun,
    Task,
    TaskPriority,
    TaskResult,
    TaskRun,
)
from task_processor.processor import (
    UNREGISTERED_RECURRING_TASK_GRACE_PERIOD,
    run_recurring_tasks,
    run_tasks,
)
from task_processor.task_registry import initialise, registered_tasks

if typing.TYPE_CHECKING:
    # This import breaks private-package-test workflow in core
    from tests.unit.task_processor.conftest import GetTaskProcessorCaplog


DEFAULT_CACHE_KEY = "foo"
DEFAULT_CACHE_VALUE = "bar"


@pytest.fixture(autouse=True)
def reset_cache() -> typing.Generator[None, None, None]:
    yield
    cache.clear()


@pytest.fixture
def dummy_task(db: None) -> TaskHandler[[str, str]]:
    @register_task_handler()
    def _dummy_task(
        key: str = DEFAULT_CACHE_KEY,
        value: str = DEFAULT_CACHE_VALUE,
    ) -> None:
        """function used to test that task is being run successfully"""
        cache.set(key, value)

    return _dummy_task


@pytest.fixture
def raise_exception_task(db: None) -> TaskHandler[[str]]:
    @register_task_handler()
    def _raise_exception_task(msg: str) -> None:
        raise Exception(msg)

    return _raise_exception_task


@pytest.fixture
def sleep_task(db: None) -> TaskHandler[[int]]:
    @register_task_handler()
    def _sleep_task(seconds: int) -> None:
        time.sleep(seconds)

    return _sleep_task


def test_run_task_runs_task_and_creates_task_run_object_when_success(
    dummy_task: TaskHandler[[str, str]],
) -> None:
    # Given
    task = Task.create(
        dummy_task.task_identifier,
        scheduled_for=timezone.now(),
    )
    task.save()

    # When
    task_runs = run_tasks()

    # Then
    assert cache.get(DEFAULT_CACHE_KEY)

    assert len(task_runs) == TaskRun.objects.filter(task=task).count() == 1
    task_run = task_runs[0]
    assert task_run.result == TaskResult.SUCCESS.value
    assert task_run.started_at
    assert task_run.finished_at
    assert task_run.error_details is None

    task.refresh_from_db()
    assert task.completed


def test_run_task_kills_task_after_timeout(
    sleep_task: TaskHandler[[int]],
    get_task_processor_caplog: "GetTaskProcessorCaplog",
) -> None:
    # Given
    caplog = get_task_processor_caplog(logging.ERROR)
    task = Task.create(
        sleep_task.task_identifier,
        scheduled_for=timezone.now(),
        args=(1,),
        timeout=timedelta(microseconds=1),
    )
    task.save()

    # When
    task_runs = run_tasks()

    # Then
    assert len(task_runs) == TaskRun.objects.filter(task=task).count() == 1
    task_run = task_runs[0]
    assert task_run.result == TaskResult.FAILURE.value
    assert task_run.started_at
    assert task_run.finished_at is None
    assert task_run.error_details
    assert "TimeoutError" in task_run.error_details

    task.refresh_from_db()

    assert task.completed is False
    assert task.num_failures == 1
    assert task.is_locked is False

    assert len(caplog.records) == 1
    assert caplog.records[0].message == (
        f"Failed to execute task '{task.task_identifier}', with id {task.id}. Exception: TimeoutError()"
    )


def test_run_recurring_task_kills_task_after_timeout(
    db: None,
    monkeypatch: MonkeyPatch,
    get_task_processor_caplog: "GetTaskProcessorCaplog",
) -> None:
    # Given
    caplog = get_task_processor_caplog(logging.ERROR)
    monkeypatch.setenv("RUN_BY_PROCESSOR", "True")

    @register_recurring_task(
        run_every=timedelta(seconds=1), timeout=timedelta(microseconds=1)
    )
    def _dummy_recurring_task() -> None:
        time.sleep(1)

    initialise()

    task = RecurringTask.objects.get(
        task_identifier="test_unit_task_processor_processor._dummy_recurring_task",
    )
    # When
    task_runs = run_recurring_tasks()

    # Then
    assert len(task_runs) == RecurringTaskRun.objects.filter(task=task).count() == 1
    task_run = task_runs[0]
    assert task_run.result == TaskResult.FAILURE.value
    assert task_run.started_at
    assert task_run.finished_at is None
    assert task_run.error_details
    assert "TimeoutError" in task_run.error_details

    task.refresh_from_db()

    assert task.locked_at is None
    assert task.is_locked is False

    assert len(caplog.records) == 1
    assert caplog.records[0].message == (
        f"Failed to execute task '{task.task_identifier}', with id {task.id}. Exception: TimeoutError()"
    )


def test_run_recurring_tasks_runs_task_and_creates_recurring_task_run_object_when_success(
    db: None,
    monkeypatch: MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("RUN_BY_PROCESSOR", "True")

    @register_recurring_task(run_every=timedelta(seconds=1))
    def _dummy_recurring_task() -> None:
        cache.set(DEFAULT_CACHE_KEY, DEFAULT_CACHE_VALUE)

    initialise()

    task = RecurringTask.objects.get(
        task_identifier="test_unit_task_processor_processor._dummy_recurring_task",
    )
    # When
    task_runs = run_recurring_tasks()

    # Then
    assert cache.get(DEFAULT_CACHE_KEY)

    assert len(task_runs) == RecurringTaskRun.objects.filter(task=task).count() == 1
    task_run = task_runs[0]
    assert task_run.result == TaskResult.SUCCESS.value
    assert task_run.started_at
    assert task_run.finished_at
    assert task_run.error_details is None


def test_run_recurring_tasks_runs_locked_task_after_tiemout(
    db: None,
    monkeypatch: MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("RUN_BY_PROCESSOR", "True")

    @register_recurring_task(run_every=timedelta(hours=1))
    def _dummy_recurring_task() -> None:
        cache.set(DEFAULT_CACHE_KEY, DEFAULT_CACHE_VALUE)

    initialise()

    task = RecurringTask.objects.get(
        task_identifier="test_unit_task_processor_processor._dummy_recurring_task",
    )
    task.is_locked = True
    task.locked_at = timezone.now() - timedelta(hours=1)
    task.save()

    # When
    assert cache.get(DEFAULT_CACHE_KEY) is None
    task_runs = run_recurring_tasks()

    # Then
    assert cache.get(DEFAULT_CACHE_KEY) == DEFAULT_CACHE_VALUE

    assert len(task_runs) == RecurringTaskRun.objects.filter(task=task).count() == 1
    task_run = task_runs[0]
    assert task_run.result == TaskResult.SUCCESS.value
    assert task_run.started_at
    assert task_run.finished_at
    assert task_run.error_details is None

    # And the task is no longer locked
    task.refresh_from_db()
    assert task.is_locked is False
    assert task.locked_at is None


@pytest.mark.django_db(transaction=True)
def test_run_recurring_tasks_multiple_runs(
    db: None,
    run_by_processor: None,
) -> None:
    # Given
    @register_recurring_task(run_every=timedelta(milliseconds=200))
    def _dummy_recurring_task() -> None:
        val = cache.get(DEFAULT_CACHE_KEY, 0) + 1
        cache.set(DEFAULT_CACHE_KEY, val)

    initialise()

    task = RecurringTask.objects.get(
        task_identifier="test_unit_task_processor_processor._dummy_recurring_task",
    )

    # When
    first_task_runs = run_recurring_tasks()

    # run the process again before the task is scheduled to run again to ensure
    # that tasks are unlocked when they are picked up by the task processor but
    # not executed.
    no_task_runs = run_recurring_tasks()

    time.sleep(0.3)

    second_task_runs = run_recurring_tasks()

    # Then
    assert len(first_task_runs) == 1
    assert len(no_task_runs) == 0
    assert len(second_task_runs) == 1

    # we should still only have 2 organisations, despite executing the
    # `run_recurring_tasks` function 3 times.
    assert cache.get(DEFAULT_CACHE_KEY) == 2

    all_task_runs = first_task_runs + second_task_runs
    assert len(all_task_runs) == RecurringTaskRun.objects.filter(task=task).count() == 2
    for task_run in all_task_runs:
        assert task_run.result == TaskResult.SUCCESS.value
        assert task_run.started_at
        assert task_run.finished_at
        assert task_run.error_details is None


@pytest.mark.django_db(transaction=True)
def test_run_recurring_tasks_loops_over_all_tasks(
    db: None,
    run_by_processor: None,
) -> None:
    # Given, Three recurring tasks
    @register_recurring_task(run_every=timedelta(milliseconds=200))
    def _dummy_recurring_task_1() -> None:
        pass

    @register_recurring_task(run_every=timedelta(milliseconds=200))
    def _dummy_recurring_task_2() -> None:
        pass

    @register_recurring_task(run_every=timedelta(milliseconds=200))
    def _dummy_recurring_task_3() -> None:
        pass

    initialise()

    # When, we call run_recurring_tasks in a loop few times
    for _ in range(4):
        run_recurring_tasks()

    # Then - we should have exactly one RecurringTaskRun for each task
    for i in range(1, 4):
        task = RecurringTask.objects.get(
            task_identifier=f"test_unit_task_processor_processor._dummy_recurring_task_{i}",
        )

        assert RecurringTaskRun.objects.filter(task=task).count() == 1


def test_run_recurring_tasks_only_executes_tasks_after_interval_set_by_run_every(
    db: None,
    run_by_processor: None,
) -> None:
    # Given
    @register_recurring_task(run_every=timedelta(milliseconds=200))
    def _dummy_recurring_task() -> None:
        val = cache.get(DEFAULT_CACHE_KEY, 0) + 1
        cache.set(DEFAULT_CACHE_KEY, val)

    initialise()

    task = RecurringTask.objects.get(
        task_identifier="test_unit_task_processor_processor._dummy_recurring_task",
    )

    # When - we call run_recurring_tasks twice
    run_recurring_tasks()
    run_recurring_tasks()

    # Then - we expect the task to have been run once

    assert cache.get(DEFAULT_CACHE_KEY) == 1

    assert RecurringTaskRun.objects.filter(task=task).count() == 1


def test_run_recurring_tasks_does_nothing_if_unregistered_task_is_new(
    db: None,
    run_by_processor: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given
    task_processor_logger = logging.getLogger("task_processor")
    task_processor_logger.propagate = True

    task_identifier = "test_unit_task_processor_processor._a_task"

    @register_recurring_task(run_every=timedelta(milliseconds=100))
    def _a_task() -> None:
        pass

    initialise()

    # now - remove the task from the registry
    from task_processor.task_registry import registered_tasks

    registered_tasks.pop(task_identifier)

    # When
    task_runs = run_recurring_tasks()

    # Then
    assert len(task_runs) == 0
    assert RecurringTask.objects.filter(task_identifier=task_identifier).exists()


def test_run_recurring_tasks_deletes_the_task_if_unregistered_task_is_old(
    db: None,
    run_by_processor: None,
    mocker: MockerFixture,
) -> None:
    # Given
    task_processor_logger = logging.getLogger("task_processor")
    task_processor_logger.propagate = True

    task_identifier = "test_unit_task_processor_processor._a_task"

    with freeze_time(timezone.now() - UNREGISTERED_RECURRING_TASK_GRACE_PERIOD):

        @register_recurring_task(run_every=timedelta(milliseconds=100))
        def _a_task() -> None:
            pass

        initialise()

    # now - remove the task from the registry
    registered_tasks.pop(task_identifier)

    # When
    task_runs = run_recurring_tasks()

    # Then
    assert len(task_runs) == 0
    assert (
        RecurringTask.objects.filter(task_identifier=task_identifier).exists() is False
    )


def test_run_task_runs_task_and_creates_task_run_object_when_failure(
    raise_exception_task: TaskHandler[[str]],
    get_task_processor_caplog: "GetTaskProcessorCaplog",
) -> None:
    # Given
    caplog = get_task_processor_caplog(logging.DEBUG)

    msg = "Error!"
    task = Task.create(
        raise_exception_task.task_identifier, args=(msg,), scheduled_for=timezone.now()
    )
    task.save()

    # When
    task_runs = run_tasks()

    # Then
    assert len(task_runs) == TaskRun.objects.filter(task=task).count() == 1
    task_run = task_runs[0]
    assert task_run.result == TaskResult.FAILURE.value
    assert task_run.started_at
    assert task_run.finished_at is None
    assert task_run.error_details is not None

    task.refresh_from_db()
    assert not task.completed

    expected_log_records = [
        ("DEBUG", "Running 1 task(s)"),
        (
            "DEBUG",
            f"Running task {task.task_identifier} id={task.id} args={task.args} kwargs={task.kwargs}",
        ),
        (
            "ERROR",
            f"Failed to execute task '{task.task_identifier}', with id {task.id}. Exception: {msg}",
        ),
        ("DEBUG", "Finished running 1 task(s)"),
    ]

    assert expected_log_records == [
        (record.levelname, record.message) for record in caplog.records
    ]


def test_run_task_runs_failed_task_again(
    raise_exception_task: TaskHandler[[str]],
) -> None:
    # Given
    task = Task.create(
        raise_exception_task.task_identifier, scheduled_for=timezone.now()
    )
    task.save()

    # When
    first_task_runs = run_tasks()

    # Now, let's run the task again
    second_task_runs = run_tasks()

    # Then
    task_runs = first_task_runs + second_task_runs
    assert len(task_runs) == TaskRun.objects.filter(task=task).count() == 2

    # Then
    for task_run in task_runs:
        assert task_run.result == TaskResult.FAILURE.value
        assert task_run.started_at
        assert task_run.finished_at is None
        assert task_run.error_details is not None

    task.refresh_from_db()
    assert task.completed is False
    assert task.is_locked is False


def test_run_recurring_task_runs_task_and_creates_recurring_task_run_object_when_failure(
    db: None,
    run_by_processor: None,
) -> None:
    # Given
    task_identifier = "test_unit_task_processor_processor._raise_exception"

    @register_recurring_task(run_every=timedelta(seconds=1))
    def _raise_exception(organisation_name: str) -> None:
        raise RuntimeError("test exception")

    initialise()

    task = RecurringTask.objects.get(task_identifier=task_identifier)

    # When
    task_runs = run_recurring_tasks()

    # Then
    assert len(task_runs) == RecurringTaskRun.objects.filter(task=task).count() == 1
    task_run = task_runs[0]
    assert task_run.result == TaskResult.FAILURE.value
    assert task_run.started_at
    assert task_run.finished_at is None
    assert task_run.error_details is not None


def test_run_task_does_nothing_if_no_tasks(db: None) -> None:
    # Given - no tasks
    # When
    result = run_tasks()
    # Then
    assert result == []
    assert not TaskRun.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_run_task_runs_tasks_in_correct_priority(
    dummy_task: TaskHandler[[str, str]],
) -> None:
    # Given
    # 2 tasks
    task_1 = Task.create(
        dummy_task.task_identifier,
        scheduled_for=timezone.now(),
        args=("task 1 organisation",),
        priority=TaskPriority.HIGH,
    )
    task_1.save()

    task_2 = Task.create(
        dummy_task.task_identifier,
        scheduled_for=timezone.now(),
        args=("task 2 organisation",),
        priority=TaskPriority.HIGH,
    )
    task_2.save()

    task_3 = Task.create(
        dummy_task.task_identifier,
        scheduled_for=timezone.now(),
        args=("task 3 organisation",),
        priority=TaskPriority.HIGHEST,
    )
    task_3.save()

    # When
    task_runs_1 = run_tasks()
    task_runs_2 = run_tasks()
    task_runs_3 = run_tasks()

    # Then
    assert task_runs_1[0].task == task_3
    assert task_runs_2[0].task == task_1
    assert task_runs_3[0].task == task_2


@pytest.mark.django_db(transaction=True)
def test_run_tasks__expected_metrics(
    dummy_task: TaskHandler[[str, str]],
    raise_exception_task: TaskHandler[[str]],
    assert_metric: AssertMetricFixture,
    mocker: MockerFixture,
) -> None:
    # Given
    dummy_task_identifier = dummy_task.task_identifier
    raise_exception_task_identifier = raise_exception_task.task_identifier
    Task.create(
        dummy_task_identifier,
        scheduled_for=timezone.now(),
        args=("arg1", "arg2"),
    ).save()
    Task.create(
        raise_exception_task_identifier,
        scheduled_for=timezone.now(),
        args=("arg1",),
    ).save()

    # When
    run_tasks(2)

    # Then
    assert_metric(
        name="task_processor_finished_tasks_total",
        value=1.0,
        labels={
            "task_identifier": dummy_task_identifier,
            "result": "success",
        },
    )
    assert_metric(
        name="task_processor_finished_tasks_total",
        value=1.0,
        labels={
            "task_identifier": raise_exception_task_identifier,
            "result": "failure",
        },
    )
    assert_metric(
        name="task_processor_task_duration_seconds",
        value=mocker.ANY,
        labels={
            "task_identifier": dummy_task_identifier,
            "result": "success",
        },
    )
    assert_metric(
        name="task_processor_task_duration_seconds",
        value=mocker.ANY,
        labels={
            "task_identifier": raise_exception_task_identifier,
            "result": "success",
        },
    )


@pytest.mark.django_db(transaction=True)
def test_run_tasks_skips_locked_tasks(
    dummy_task: TaskHandler[[str, str]],
    sleep_task: TaskHandler[[int]],
) -> None:
    """
    This test verifies that tasks are locked while being executed, and hence
    new task runners are not able to pick up 'in progress' tasks.
    """
    # Given
    # 2 tasks
    # One which is configured to just sleep for 3 seconds, to simulate a task
    # being held for a short period of time
    task_1 = Task.create(
        sleep_task.task_identifier, scheduled_for=timezone.now(), args=(3,)
    )
    task_1.save()

    # and another which should create an organisation
    task_2 = Task.create(
        dummy_task.task_identifier,
        scheduled_for=timezone.now(),
        args=("task 2 organisation",),
    )
    task_2.save()

    # When
    # we spawn a new thread to run the first task (configured to just sleep)
    task_runner_thread = Thread(target=run_tasks)
    task_runner_thread.start()

    # and subsequently attempt to run another task in the main thread
    time.sleep(1)  # wait for the thread to start and hold the task
    task_runs = run_tasks()

    # Then
    # the second task is run while the 1st task is held
    assert task_runs[0].task == task_2

    task_runner_thread.join()


def test_run_more_than_one_task(dummy_task: TaskHandler[[str, str]]) -> None:
    # Given
    num_tasks = 5

    tasks = []
    for _ in range(num_tasks):
        organisation_name = f"test-org-{uuid.uuid4()}"
        tasks.append(
            Task.create(
                dummy_task.task_identifier,
                scheduled_for=timezone.now(),
                args=(organisation_name,),
            )
        )
    Task.objects.bulk_create(tasks)

    # When
    task_runs = run_tasks(5)

    # Then
    assert len(task_runs) == num_tasks

    for task_run in task_runs:
        assert task_run.result == TaskResult.SUCCESS.value
        assert task_run.started_at
        assert task_run.finished_at
        assert task_run.error_details is None

    for task in tasks:
        task.refresh_from_db()
        assert task.completed


def test_recurring_tasks_are_unlocked_if_picked_up_but_not_executed(
    db: None,
    run_by_processor: None,
) -> None:
    # Given
    @register_recurring_task(run_every=timedelta(days=1))
    def my_task() -> None:
        pass

    initialise()

    recurring_task = RecurringTask.objects.get(
        task_identifier="test_unit_task_processor_processor.my_task"
    )

    # mimic the task having already been run so that it is next picked up,
    # but not executed
    now = timezone.now()
    one_minute_ago = now - timedelta(minutes=1)
    RecurringTaskRun.objects.create(
        task=recurring_task,
        started_at=one_minute_ago,
        finished_at=now,
        result=TaskResult.SUCCESS.name,
    )

    # When
    run_recurring_tasks()

    # Then
    recurring_task.refresh_from_db()
    assert recurring_task.is_locked is False
