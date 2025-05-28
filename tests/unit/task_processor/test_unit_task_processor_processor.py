import logging
import time
import uuid
from datetime import datetime, timedelta
from threading import Thread

import pytest
from django.core.cache import cache
from django.utils import timezone
from freezegun import freeze_time
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from common.test_tools.types import AssertMetricFixture
from task_processor.decorators import (
    TaskHandler,
    register_recurring_task,
    register_task_handler,
)
from task_processor.exceptions import TaskBackoffError
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

DEFAULT_CACHE_KEY = "foo"
DEFAULT_CACHE_VALUE = "bar"


@pytest.fixture(autouse=True)
def reset_cache() -> None:
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


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_task_runs_task_and_creates_task_run_object_when_success(
    current_database: str,
    dummy_task: TaskHandler[[str, str]],
) -> None:
    # Given
    task = Task.create(dummy_task.task_identifier, scheduled_for=timezone.now())
    task.save(using=current_database)

    # When
    task_runs = run_tasks(current_database)

    # Then
    assert cache.get(DEFAULT_CACHE_KEY)

    assert (
        len(task_runs)
        == TaskRun.objects.using(current_database).filter(task=task).count()
        == 1
    )
    task_run = task_runs[0]
    assert task_run.result == TaskResult.SUCCESS.value
    assert task_run.started_at
    assert task_run.finished_at
    assert task_run.error_details is None

    task.refresh_from_db(using=current_database)
    assert task.completed


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_task_kills_task_after_timeout(
    caplog: pytest.LogCaptureFixture,
    current_database: str,
    sleep_task: TaskHandler[[int]],
) -> None:
    # Given
    task = Task.create(
        sleep_task.task_identifier,
        scheduled_for=timezone.now(),
        args=(1,),
        timeout=timedelta(microseconds=1),
    )
    task.save(using=current_database)

    # When
    task_runs = run_tasks(current_database)

    # Then
    assert (
        len(task_runs)
        == TaskRun.objects.using(current_database).filter(task=task).count()
        == 1
    )
    task_run = task_runs[0]
    assert task_run.result == TaskResult.FAILURE.value
    assert task_run.started_at
    assert task_run.finished_at is None
    assert task_run.error_details
    assert "TimeoutError" in task_run.error_details

    task.refresh_from_db(using=current_database)

    assert task.completed is False
    assert task.num_failures == 1
    assert task.is_locked is False

    assert len(caplog.records) == 1
    assert caplog.records[0].message == (
        f"Failed to execute task '{task.task_identifier}', with id {task.id}. Exception: TimeoutError()"
    )


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_recurring_task_kills_task_after_timeout(
    caplog: pytest.LogCaptureFixture,
    current_database: str,
    settings: SettingsWrapper,
) -> None:
    # Given
    @register_recurring_task(
        run_every=timedelta(seconds=1), timeout=timedelta(microseconds=1)
    )
    def _dummy_recurring_task() -> None:
        time.sleep(1)

    initialise()

    task = RecurringTask.objects.using(current_database).get(
        task_identifier="test_unit_task_processor_processor._dummy_recurring_task",
    )
    # When
    task_runs = run_recurring_tasks(current_database)

    # Then
    assert (
        len(task_runs)
        == RecurringTaskRun.objects.using(current_database).filter(task=task).count()
        == 1
    )
    task_run = task_runs[0]
    assert task_run.result == TaskResult.FAILURE.value
    assert task_run.started_at
    assert task_run.finished_at is None
    assert task_run.error_details
    assert "TimeoutError" in task_run.error_details

    task.refresh_from_db(using=current_database)

    assert task.locked_at is None
    assert task.is_locked is False

    assert len(caplog.records) == 1
    assert caplog.records[0].message == (
        f"Failed to execute task '{task.task_identifier}', with id {task.id}. Exception: TimeoutError()"
    )


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_recurring_tasks_runs_task_and_creates_recurring_task_run_object_when_success(
    current_database: str,
    settings: SettingsWrapper,
) -> None:
    # Given
    @register_recurring_task(run_every=timedelta(seconds=1))
    def _dummy_recurring_task() -> None:
        cache.set(DEFAULT_CACHE_KEY, DEFAULT_CACHE_VALUE)

    initialise()

    task = RecurringTask.objects.using(current_database).get(
        task_identifier="test_unit_task_processor_processor._dummy_recurring_task",
    )
    # When
    task_runs = run_recurring_tasks(current_database)

    # Then
    assert cache.get(DEFAULT_CACHE_KEY)

    assert (
        len(task_runs)
        == RecurringTaskRun.objects.using(current_database).filter(task=task).count()
        == 1
    )
    task_run = task_runs[0]
    assert task_run.result == TaskResult.SUCCESS.value
    assert task_run.started_at
    assert task_run.finished_at
    assert task_run.error_details is None


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_recurring_tasks_runs_locked_task_after_timeout(
    current_database: str,
    settings: SettingsWrapper,
) -> None:
    # Given
    @register_recurring_task(run_every=timedelta(hours=1))
    def _dummy_recurring_task() -> None:
        cache.set(DEFAULT_CACHE_KEY, DEFAULT_CACHE_VALUE)

    initialise()

    task = RecurringTask.objects.using(current_database).get(
        task_identifier="test_unit_task_processor_processor._dummy_recurring_task",
    )
    task.is_locked = True
    task.locked_at = timezone.now() - timedelta(hours=1)
    task.save(using=current_database)

    # When
    assert cache.get(DEFAULT_CACHE_KEY) is None
    task_runs = run_recurring_tasks(current_database)

    # Then
    assert cache.get(DEFAULT_CACHE_KEY) == DEFAULT_CACHE_VALUE

    assert (
        len(task_runs)
        == RecurringTaskRun.objects.using(current_database).filter(task=task).count()
        == 1
    )
    task_run = task_runs[0]
    assert task_run.result == TaskResult.SUCCESS.value
    assert task_run.started_at
    assert task_run.finished_at
    assert task_run.error_details is None

    # And the task is no longer locked
    task.refresh_from_db(using=current_database)
    assert task.is_locked is False
    assert task.locked_at is None


@pytest.mark.multi_database(transaction=True)
@pytest.mark.task_processor_mode
def test_run_recurring_tasks_multiple_runs(
    current_database: str,
    settings: SettingsWrapper,
) -> None:
    # Given
    @register_recurring_task(run_every=timedelta(milliseconds=200))
    def _dummy_recurring_task() -> None:
        val = cache.get(DEFAULT_CACHE_KEY, 0) + 1
        cache.set(DEFAULT_CACHE_KEY, val)

    initialise()

    task = RecurringTask.objects.using(current_database).get(
        task_identifier="test_unit_task_processor_processor._dummy_recurring_task",
    )

    # When
    first_task_runs = run_recurring_tasks(current_database)

    # run the process again before the task is scheduled to run again to ensure
    # that tasks are unlocked when they are picked up by the task processor but
    # not executed.
    no_task_runs = run_recurring_tasks(current_database)

    time.sleep(0.3)

    second_task_runs = run_recurring_tasks(current_database)

    # Then
    assert len(first_task_runs) == 1
    assert len(no_task_runs) == 0
    assert len(second_task_runs) == 1

    # we should still only have 2 organisations, despite executing the
    # `run_recurring_tasks` function 3 times.
    assert cache.get(DEFAULT_CACHE_KEY) == 2

    all_task_runs = first_task_runs + second_task_runs
    assert (
        len(all_task_runs)
        == RecurringTaskRun.objects.using(current_database).filter(task=task).count()
        == 2
    )
    for task_run in all_task_runs:
        assert task_run.result == TaskResult.SUCCESS.value
        assert task_run.started_at
        assert task_run.finished_at
        assert task_run.error_details is None


@pytest.mark.multi_database(transaction=True)
@pytest.mark.task_processor_mode
def test_run_recurring_tasks_loops_over_all_tasks(
    current_database: str,
    settings: SettingsWrapper,
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
        run_recurring_tasks(current_database)

    # Then - we should have exactly one RecurringTaskRun for each task
    for i in range(1, 4):
        task_identifier = (
            f"test_unit_task_processor_processor._dummy_recurring_task_{i}"
        )
        assert (
            RecurringTaskRun.objects.using(current_database)
            .filter(task__task_identifier=task_identifier)
            .count()
            == 1
        )


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_recurring_tasks_only_executes_tasks_after_interval_set_by_run_every(
    current_database: str,
    settings: SettingsWrapper,
) -> None:
    # Given
    @register_recurring_task(run_every=timedelta(milliseconds=200))
    def _dummy_recurring_task() -> None:
        val = cache.get(DEFAULT_CACHE_KEY, 0) + 1
        cache.set(DEFAULT_CACHE_KEY, val)

    initialise()

    task = RecurringTask.objects.using(current_database).get(
        task_identifier="test_unit_task_processor_processor._dummy_recurring_task",
    )

    # When - we call run_recurring_tasks twice
    run_recurring_tasks(current_database)
    run_recurring_tasks(current_database)

    # Then - we expect the task to have been run once

    assert cache.get(DEFAULT_CACHE_KEY) == 1

    assert (
        RecurringTaskRun.objects.using(current_database).filter(task=task).count() == 1
    )


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_recurring_tasks_does_nothing_if_unregistered_task_is_new(
    current_database: str,
    settings: SettingsWrapper,
) -> None:
    # Given
    task_identifier = "test_unit_task_processor_processor._a_task"

    @register_recurring_task(run_every=timedelta(milliseconds=100))
    def _a_task() -> None:
        pass

    initialise()

    # now - remove the task from the registry
    from task_processor.task_registry import registered_tasks

    registered_tasks.pop(task_identifier)

    # When
    task_runs = run_recurring_tasks(current_database)

    # Then
    assert len(task_runs) == 0
    assert (
        RecurringTask.objects.using(current_database)
        .filter(task_identifier=task_identifier)
        .exists()
    )


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_recurring_tasks_deletes_the_task_if_unregistered_task_is_old(
    current_database: str,
    settings: SettingsWrapper,
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
    task_runs = run_recurring_tasks(current_database)

    # Then
    assert len(task_runs) == 0
    assert not (
        RecurringTask.objects.using(current_database)
        .filter(task_identifier=task_identifier)
        .exists()
    )


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_task_runs_task_and_creates_task_run_object_when_failure(
    caplog: pytest.LogCaptureFixture,
    current_database: str,
    raise_exception_task: TaskHandler[[str]],
) -> None:
    # Given
    caplog.set_level(logging.DEBUG)
    msg = "Error!"
    task = Task.create(
        raise_exception_task.task_identifier, args=(msg,), scheduled_for=timezone.now()
    )
    task.save(using=current_database)

    # When
    task_runs = run_tasks(current_database)

    # Then
    assert (
        len(task_runs)
        == TaskRun.objects.using(current_database).filter(task=task).count()
        == 1
    )
    task_run = task_runs[0]
    assert task_run.result == TaskResult.FAILURE.value
    assert task_run.started_at
    assert task_run.finished_at is None
    assert task_run.error_details is not None

    task.refresh_from_db(using=current_database)
    assert not task.completed

    logs = [(record.levelno, record.message) for record in caplog.records]
    assert logs == [
        (
            logging.DEBUG,
            f"Running 1 task(s) from database '{current_database}'",
        ),
        (
            logging.DEBUG,
            f"Running task {task.task_identifier} id={task.id} args=('{msg}',) kwargs={{}}",
        ),
        (
            logging.ERROR,
            f"Failed to execute task '{task.task_identifier}', with id {task.id}. Exception: {msg}",
        ),
        (
            logging.DEBUG,
            f"Finished running 1 task(s) from database '{current_database}'",
        ),
    ]


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_task_runs_failed_task_again(
    current_database: str,
    raise_exception_task: TaskHandler[[str]],
) -> None:
    # Given
    task = Task.create(
        raise_exception_task.task_identifier, scheduled_for=timezone.now()
    )
    task.save(using=current_database)

    # When
    first_task_runs = run_tasks(current_database)

    # Now, let's run the task again
    second_task_runs = run_tasks(current_database)

    # Then
    task_runs = first_task_runs + second_task_runs
    assert (
        len(task_runs)
        == TaskRun.objects.using(current_database).filter(task=task).count()
        == 2
    )

    # Then
    for task_run in task_runs:
        assert task_run.result == TaskResult.FAILURE.value
        assert task_run.started_at
        assert task_run.finished_at is None
        assert task_run.error_details is not None

    task.refresh_from_db(using=current_database)
    assert task.completed is False
    assert task.is_locked is False


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_recurring_task_runs_task_and_creates_recurring_task_run_object_when_failure(
    current_database: str,
) -> None:
    # Given
    task_identifier = "test_unit_task_processor_processor._raise_exception"

    @register_recurring_task(run_every=timedelta(seconds=1))
    def _raise_exception(organisation_name: str) -> None:
        raise RuntimeError("test exception")

    initialise()

    task = RecurringTask.objects.get(task_identifier=task_identifier)

    # When
    task_runs = run_recurring_tasks(current_database)

    # Then
    assert len(task_runs) == RecurringTaskRun.objects.filter(task=task).count() == 1
    task_run = task_runs[0]
    assert task_run.result == TaskResult.FAILURE.value
    assert task_run.started_at
    assert task_run.finished_at is None
    assert task_run.error_details is not None


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_task_does_nothing_if_no_tasks(current_database: str) -> None:
    # Given - no tasks
    pass

    # When
    result = run_tasks(current_database)

    # Then
    assert result == []
    assert not TaskRun.objects.using(current_database).exists()


@pytest.mark.multi_database(transaction=True)
@pytest.mark.task_processor_mode
def test_run_task_runs_tasks_in_correct_priority(
    current_database: str,
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
    task_1.save(using=current_database)

    task_2 = Task.create(
        dummy_task.task_identifier,
        scheduled_for=timezone.now(),
        args=("task 2 organisation",),
        priority=TaskPriority.HIGH,
    )
    task_2.save(using=current_database)

    task_3 = Task.create(
        dummy_task.task_identifier,
        scheduled_for=timezone.now(),
        args=("task 3 organisation",),
        priority=TaskPriority.HIGHEST,
    )
    task_3.save(using=current_database)

    # When
    task_runs_1 = run_tasks(current_database)
    task_runs_2 = run_tasks(current_database)
    task_runs_3 = run_tasks(current_database)

    # Then
    assert task_runs_1[0].task == task_3
    assert task_runs_2[0].task == task_1
    assert task_runs_3[0].task == task_2


@pytest.mark.parametrize(
    "exception, expected_scheduled_for",
    [
        (TaskBackoffError(), datetime.fromisoformat("2023-12-08T06:05:57+00:00")),
        (
            TaskBackoffError(
                delay_until=datetime.fromisoformat("2023-12-08T06:15:52+00:00")
            ),
            datetime.fromisoformat("2023-12-08T06:15:52+00:00"),
        ),
    ],
)
@pytest.mark.freeze_time("2023-12-08T06:05:47+00:00")
@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_task__backoff__persists_expected(
    exception: TaskBackoffError,
    expected_scheduled_for: datetime,
    current_database: str,
    settings: SettingsWrapper,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given
    settings.TASK_BACKOFF_DEFAULT_DELAY_SECONDS = 10

    @register_task_handler()
    def backoff_task() -> None:
        raise exception

    task = Task.create(
        backoff_task.task_identifier,
        scheduled_for=timezone.now(),
        args=(),
        priority=TaskPriority.HIGH,
    )
    task.save(using=current_database)

    caplog.set_level(logging.INFO)
    expected_log_message = f"Backoff requested. Task '{backoff_task.task_identifier}' set to retry at {expected_scheduled_for}"

    # When
    run_tasks(current_database)

    # Then
    assert [
        record.message for record in caplog.records if record.levelno == logging.INFO
    ] == [expected_log_message]
    task.refresh_from_db(using=current_database)
    assert task.scheduled_for == expected_scheduled_for


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_task__backoff__recurring__raises_expected(
    current_database: str,
) -> None:
    # Given
    @register_recurring_task(run_every=timedelta(seconds=1))
    def backoff_task() -> None:
        raise TaskBackoffError()

    initialise()

    # When & Then
    with pytest.raises(AssertionError) as exc_info:
        run_recurring_tasks(current_database)

    assert (
        str(exc_info.value)
        == "Attempt to back off a recurring task (currently not supported)"
    )


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_task__backoff__max_num_failures__noop(
    current_database: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given
    @register_task_handler()
    def backoff_task() -> None:
        raise TaskBackoffError()

    expected_scheduled_for = timezone.now()
    task = Task.create(
        backoff_task.task_identifier,
        scheduled_for=expected_scheduled_for,
        args=(),
        priority=TaskPriority.HIGH,
    )
    task.num_failures = 4
    task.save(using=current_database)

    caplog.set_level(logging.INFO)

    # When
    run_tasks(current_database)

    # Then
    task.refresh_from_db(using=current_database)
    assert task.scheduled_for == expected_scheduled_for
    assert not [record for record in caplog.records if record.levelno == logging.INFO]


@pytest.mark.multi_database
def test_run_tasks__fails_if_not_in_task_processor_mode(
    current_database: str,
    dummy_task: TaskHandler[[str, str]],
) -> None:
    # Given
    Task.create(
        dummy_task.task_identifier,
        scheduled_for=timezone.now(),
        args=("arg1", "arg2"),
    ).save(using=current_database)

    # When
    with pytest.raises(AssertionError):
        run_tasks(current_database)


@pytest.mark.multi_database(transaction=True)
@pytest.mark.task_processor_mode
def test_run_tasks__expected_metrics(
    assert_metric: AssertMetricFixture,
    current_database: str,
    dummy_task: TaskHandler[[str, str]],
    mocker: MockerFixture,
    raise_exception_task: TaskHandler[[str]],
    settings: SettingsWrapper,
) -> None:
    # Given
    @register_recurring_task(run_every=timedelta(milliseconds=200))
    def _fake_recurring_task() -> None:
        pass

    initialise()

    dummy_task_identifier = dummy_task.task_identifier
    raise_exception_task_identifier = raise_exception_task.task_identifier
    recurring_task_identifier = (
        RecurringTask.objects.using(current_database)
        .latest("created_at")
        .task_identifier
    )

    Task.create(
        dummy_task_identifier,
        scheduled_for=timezone.now(),
        args=("arg1", "arg2"),
    ).save(using=current_database)
    Task.create(
        raise_exception_task_identifier,
        scheduled_for=timezone.now(),
        args=("arg1",),
    ).save(using=current_database)

    # When
    run_tasks(current_database, 2)
    run_recurring_tasks(current_database)

    # Then
    assert_metric(
        name="flagsmith_task_processor_finished_tasks_total",
        value=1.0,
        labels={
            "task_identifier": dummy_task_identifier,
            "task_type": "standard",
            "result": "success",
        },
    )
    assert_metric(
        name="flagsmith_task_processor_finished_tasks_total",
        value=1.0,
        labels={
            "task_identifier": raise_exception_task_identifier,
            "task_type": "standard",
            "result": "failure",
        },
    )
    assert_metric(
        name="flagsmith_task_processor_finished_tasks_total",
        value=1.0,
        labels={
            "task_identifier": recurring_task_identifier,
            "task_type": "recurring",
            "result": "success",
        },
    )
    assert_metric(
        name="flagsmith_task_processor_task_duration_seconds",
        value=mocker.ANY,
        labels={
            "task_identifier": dummy_task_identifier,
            "task_type": "standard",
            "result": "success",
        },
    )
    assert_metric(
        name="flagsmith_task_processor_task_duration_seconds",
        value=mocker.ANY,
        labels={
            "task_identifier": raise_exception_task_identifier,
            "task_type": "standard",
            "result": "failure",
        },
    )
    assert_metric(
        name="flagsmith_task_processor_task_duration_seconds",
        value=mocker.ANY,
        labels={
            "task_identifier": recurring_task_identifier,
            "task_type": "recurring",
            "result": "success",
        },
    )


@pytest.mark.multi_database(transaction=True)
@pytest.mark.task_processor_mode
def test_run_tasks_skips_locked_tasks(
    current_database: str,
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
    task_1.save(using=current_database)

    # and another which should create an organisation
    task_2 = Task.create(
        dummy_task.task_identifier,
        scheduled_for=timezone.now(),
        args=("task 2 organisation",),
    )
    task_2.save(using=current_database)

    # When
    # we spawn a new thread to run the first task (configured to just sleep)
    task_runner_thread = Thread(target=run_tasks, args=(current_database,))
    task_runner_thread.start()

    # and subsequently attempt to run another task in the main thread
    time.sleep(1)  # wait for the thread to start and hold the task
    task_runs = run_tasks(current_database)

    # Then
    # the second task is run while the 1st task is held
    assert task_runs[0].task == task_2

    task_runner_thread.join()


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_run_more_than_one_task(
    current_database: str,
    dummy_task: TaskHandler[[str, str]],
) -> None:
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
    Task.objects.using(current_database).bulk_create(tasks)

    # When
    task_runs = run_tasks(current_database, 5)

    # Then
    assert len(task_runs) == num_tasks

    for task_run in task_runs:
        assert task_run.result == TaskResult.SUCCESS.value
        assert task_run.started_at
        assert task_run.finished_at
        assert task_run.error_details is None

    for task in tasks:
        task.refresh_from_db(using=current_database)
        assert task.completed


@pytest.mark.multi_database
@pytest.mark.task_processor_mode
def test_recurring_tasks_are_unlocked_if_picked_up_but_not_executed(
    current_database: str,
    settings: SettingsWrapper,
) -> None:
    # Given
    @register_recurring_task(run_every=timedelta(days=1))
    def my_task() -> None:
        pass

    initialise()

    recurring_task = RecurringTask.objects.using(current_database).get(
        task_identifier="test_unit_task_processor_processor.my_task"
    )

    # mimic the task having already been run so that it is next picked up,
    # but not executed
    now = timezone.now()
    one_minute_ago = now - timedelta(minutes=1)
    RecurringTaskRun.objects.using(current_database).create(
        task=recurring_task,
        started_at=one_minute_ago,
        finished_at=now,
        result=TaskResult.SUCCESS.name,
    )

    # When
    run_recurring_tasks(current_database)

    # Then
    recurring_task.refresh_from_db(using=current_database)
    assert recurring_task.is_locked is False
