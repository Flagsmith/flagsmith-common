from django.utils import timezone

from task_processor.models import Task


def get_num_waiting_tasks() -> int:
    return Task.objects.filter(
        num_failures__lt=3,
        completed=False,
        scheduled_for__lt=timezone.now(),
        is_locked=False,
    ).count()
