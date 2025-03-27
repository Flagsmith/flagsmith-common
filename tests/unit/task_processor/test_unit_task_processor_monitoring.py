from datetime import timedelta

from django.utils import timezone

from task_processor.models import Task
from task_processor.monitoring import get_num_waiting_tasks


def test_get_num_waiting_tasks(db: None) -> None:
    # Given
    now = timezone.now()

    # a task that is waiting
    Task.objects.create(task_identifier="tasks.test_task")

    # a task that is scheduled for the future
    Task.objects.create(
        task_identifier="tasks.test_task", scheduled_for=now + timedelta(days=1)
    )

    # and a task that has been completed
    Task.objects.create(
        task_identifier="tasks.test_task",
        scheduled_for=now - timedelta(days=1),
        completed=True,
    )

    # and a task that has been locked for processing
    Task.objects.create(
        task_identifier="tasks.test_task",
        is_locked=True,
    )

    # When
    num_waiting_tasks = get_num_waiting_tasks()

    # Then
    assert num_waiting_tasks == 1
