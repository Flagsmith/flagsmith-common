from datetime import timedelta

import pytest
from django.utils import timezone
from pytest_django.fixtures import DjangoAssertNumQueries, SettingsWrapper

from task_processor.models import RecurringTask, RecurringTaskRun, Task
from task_processor.tasks import (
    clean_up_old_recurring_task_runs,
    clean_up_old_tasks,
)

now = timezone.now()
three_days_ago = now - timedelta(days=3)
one_day_ago = now - timedelta(days=1)
one_hour_from_now = now + timedelta(hours=1)
sixty_days_ago = now - timedelta(days=60)


@pytest.mark.django_db
def test_clean_up_old_tasks__no_tasks__does_nothing() -> None:
    # Given
    assert Task.objects.count() == 0

    # When
    clean_up_old_tasks()

    # Then
    assert Task.objects.count() == 0


def test_clean_up_old_recurring_task_runs__no_runs__does_nothing(db: None) -> None:
    # Given
    assert RecurringTaskRun.objects.count() == 0

    # When
    clean_up_old_recurring_task_runs()

    # Then
    assert RecurringTaskRun.objects.count() == 0


@pytest.mark.django_db
def test_clean_up_old_tasks__tasks_exist__deletes_old_completed(
    settings: SettingsWrapper,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    settings.TASK_DELETE_RETENTION_DAYS = 2
    settings.TASK_DELETE_BATCH_SIZE = 1

    # 2 completed tasks that were scheduled before retention period
    for _ in range(2):
        Task.objects.create(
            task_identifier="some.identifier",
            scheduled_for=three_days_ago,
            completed=True,
        )

    # a task that has been completed but is within the retention period
    task_in_retention_period = Task.objects.create(
        task_identifier="some.identifier", scheduled_for=one_day_ago, completed=True
    )

    # and a task that has yet to be completed
    future_task = Task.objects.create(
        task_identifier="some.identifier", scheduled_for=one_hour_from_now
    )

    # and a task that failed
    failed_task = Task.objects.create(
        task_identifier="some.identifier", scheduled_for=three_days_ago, num_failures=3
    )

    # When
    with django_assert_num_queries(7):
        # We expect 9 queries to be run here since we have set the delete batch size to 1 and there are 2
        # tasks we expect it to delete. Therefore, we have 2 loops, each consisting of 3 queries:
        #  1. Grab the ids of any matching tasks
        #  2. Delete all TaskRun objects for those task_id values
        #  3. Delete all Task objects for those ids
        #
        # The final (7th) query is checking if any tasks match the delete filter (which returns false).
        clean_up_old_tasks()

    # Then
    assert list(Task.objects.all()) == [
        task_in_retention_period,
        future_task,
        failed_task,
    ]


@pytest.mark.django_db
def test_clean_up_old_recurring_task_runs__runs_exist__deletes_old(
    settings: SettingsWrapper,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    settings.RECURRING_TASK_RUN_RETENTION_DAYS = 2
    settings.ENABLE_CLEAN_UP_OLD_TASKS = True

    recurring_task = RecurringTask.objects.create(
        task_identifier="some_identifier", run_every=timedelta(seconds=1)
    )

    # 2 task runs finished before retention period
    for _ in range(2):
        RecurringTaskRun.objects.create(
            started_at=three_days_ago,
            task=recurring_task,
            finished_at=three_days_ago,
        )

    # a task run that is within the retention period
    task_in_retention_period = RecurringTaskRun.objects.create(
        task=recurring_task,
        started_at=one_day_ago,
        finished_at=one_day_ago,
    )

    # When
    with django_assert_num_queries(1):
        clean_up_old_recurring_task_runs()

    # Then
    assert list(RecurringTaskRun.objects.all()) == [task_in_retention_period]


@pytest.mark.django_db
def test_clean_up_old_tasks__include_failed_enabled__deletes_failed(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.TASK_DELETE_RETENTION_DAYS = 2
    settings.TASK_DELETE_INCLUDE_FAILED_TASKS = True

    # a task that failed
    Task.objects.create(
        task_identifier="some.identifier", scheduled_for=three_days_ago, num_failures=3
    )

    # When
    clean_up_old_tasks()

    # Then
    assert not Task.objects.exists()


@pytest.mark.django_db
def test_clean_up_old_tasks__disabled__does_not_run(
    settings: SettingsWrapper,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    settings.ENABLE_CLEAN_UP_OLD_TASKS = False

    task = Task.objects.create(
        task_identifier="some.identifier", scheduled_for=sixty_days_ago
    )

    # When
    with django_assert_num_queries(0):
        clean_up_old_tasks()

    # Then
    assert Task.objects.filter(id=task.id).exists()


@pytest.mark.django_db
def test_clean_up_old_recurring_task_runs__disabled__does_not_run(
    settings: SettingsWrapper,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    settings.RECURRING_TASK_RUN_RETENTION_DAYS = 2
    settings.ENABLE_CLEAN_UP_OLD_TASKS = False

    recurring_task = RecurringTask.objects.create(
        task_identifier="some_identifier", run_every=timedelta(seconds=1)
    )

    RecurringTaskRun.objects.create(
        started_at=three_days_ago,
        task=recurring_task,
        finished_at=three_days_ago,
    )

    # When
    with django_assert_num_queries(0):
        clean_up_old_recurring_task_runs()

    # Then
    assert RecurringTaskRun.objects.exists()
