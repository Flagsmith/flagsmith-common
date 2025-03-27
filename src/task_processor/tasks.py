import logging
import typing
from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)
from task_processor.models import HealthCheckModel, RecurringTaskRun, Task

if typing.TYPE_CHECKING:
    # ugh https://github.com/typeddjango/django-stubs/issues/1744
    # TODO maybe switch to https://github.com/getsentry/sentry-forked-django-stubs
    HealthCheckModel.objects = HealthCheckModel._default_manager
    RecurringTaskRun.objects = RecurringTaskRun._default_manager


logger = logging.getLogger(__name__)


@register_task_handler()
def create_health_check_model(health_check_model_uuid: str) -> None:
    logger.info("Creating health check model.")
    HealthCheckModel.objects.create(uuid=health_check_model_uuid)


@register_recurring_task(
    run_every=settings.TASK_DELETE_RUN_EVERY,
    first_run_time=settings.TASK_DELETE_RUN_TIME,
)
def clean_up_old_tasks() -> None:
    if not settings.ENABLE_CLEAN_UP_OLD_TASKS:
        return

    now = timezone.now()
    delete_before = now - timedelta(days=settings.TASK_DELETE_RETENTION_DAYS)

    # build the query
    query = Q(completed=True)
    if settings.TASK_DELETE_INCLUDE_FAILED_TASKS:
        query = query | Q(num_failures__gte=3)
    query = Q(scheduled_for__lt=delete_before) & query

    # TODO: validate if deleting in batches is more / less impactful on the DB
    while True:
        # delete in batches of settings.TASK_DELETE_BATCH_SIZE
        num_tasks_deleted, _ = Task.objects.filter(
            pk__in=Task.objects.filter(query).values_list("id", flat=True)[
                0 : settings.TASK_DELETE_BATCH_SIZE  # noqa:E203
            ]
        ).delete()
        if num_tasks_deleted == 0:
            break


@register_recurring_task(
    run_every=settings.TASK_DELETE_RUN_EVERY,
    first_run_time=settings.TASK_DELETE_RUN_TIME,
)
def clean_up_old_recurring_task_runs() -> None:
    if not settings.ENABLE_CLEAN_UP_OLD_TASKS:
        return

    now = timezone.now()
    delete_before = now - timedelta(days=settings.RECURRING_TASK_RUN_RETENTION_DAYS)

    RecurringTaskRun.objects.filter(finished_at__lt=delete_before).delete()
