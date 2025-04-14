import logging
import traceback
import typing
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from task_processor import metrics
from task_processor.models import (
    AbstractBaseTask,
    RecurringTask,
    RecurringTaskRun,
    Task,
    TaskResult,
    TaskRun,
)
from task_processor.task_registry import get_task

T = typing.TypeVar("T", bound=AbstractBaseTask)
AnyTaskRun = TaskRun | RecurringTaskRun

logger = logging.getLogger(__name__)

UNREGISTERED_RECURRING_TASK_GRACE_PERIOD = timedelta(minutes=30)


def run_tasks(num_tasks: int = 1) -> list[TaskRun]:
    if num_tasks < 1:
        raise ValueError("Number of tasks to process must be at least one")

    tasks = Task.objects.get_tasks_to_process(num_tasks)

    if tasks:
        logger.debug(f"Running {len(tasks)} task(s)")

        executed_tasks = []
        task_runs = []

        for task in tasks:
            task, task_run = _run_task(task)

            executed_tasks.append(task)
            assert isinstance(task_run, TaskRun)
            task_runs.append(task_run)

        if executed_tasks:
            Task.objects.bulk_update(
                executed_tasks,
                fields=["completed", "num_failures", "is_locked"],
            )

        if task_runs:
            TaskRun.objects.bulk_create(task_runs)
            logger.debug(f"Finished running {len(task_runs)} task(s)")

        return task_runs

    return []


def run_recurring_tasks() -> list[RecurringTaskRun]:
    # NOTE: We will probably see a lot of delay in the execution of recurring tasks
    # if the tasks take longer then `run_every` to execute. This is not
    # a problem for now, but we should be mindful of this limitation
    tasks = RecurringTask.objects.get_tasks_to_process()
    if tasks:
        logger.debug(f"Running {len(tasks)} recurring task(s)")

        task_runs = []

        for task in tasks:
            if not task.is_task_registered:
                # This is necessary to ensure that old instances of the task processor,
                # which may still be running during deployment, do not remove tasks added by new instances.
                # Reference: https://github.com/Flagsmith/flagsmith/issues/2551
                if (
                    timezone.now() - task.created_at
                ) > UNREGISTERED_RECURRING_TASK_GRACE_PERIOD:
                    task.delete()
                continue

            if task.should_execute:
                task, task_run = _run_task(task)
                assert isinstance(task_run, RecurringTaskRun)
                task_runs.append(task_run)
            else:
                task.unlock()

        # update all tasks that were not deleted
        to_update = [task for task in tasks if task.id]
        RecurringTask.objects.bulk_update(to_update, fields=["is_locked", "locked_at"])

        if task_runs:
            RecurringTaskRun.objects.bulk_create(task_runs)
            logger.debug(f"Finished running {len(task_runs)} recurring task(s)")

        return task_runs

    return []


def _run_task(
    task: T,
) -> typing.Tuple[T, AnyTaskRun]:
    assert settings.TASK_PROCESSOR_MODE, (
        "Attempt to run tasks in a non-task-processor environment"
    )

    ctx = ExitStack()
    timer = metrics.flagsmith_task_processor_task_duration_seconds.time()
    ctx.enter_context(timer)

    task_identifier = task.task_identifier

    logger.debug(
        f"Running task {task_identifier} id={task.pk} args={task.args} kwargs={task.kwargs}"
    )
    task_run: AnyTaskRun = task.task_runs.model(started_at=timezone.now(), task=task)  # type: ignore[attr-defined]
    result: str

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(task.run)
            timeout = task.timeout.total_seconds() if task.timeout else None
            future.result(timeout=timeout)  # Wait for completion or timeout

        task_run.result = result = TaskResult.SUCCESS.value
        task_run.finished_at = timezone.now()
        task.mark_success()

        logger.debug(f"Task {task_identifier} id={task.pk} completed")

    except Exception as e:
        # For errors that don't include a default message (e.g., TimeoutError),
        # fall back to using repr.
        err_msg = str(e) or repr(e)

        task.mark_failure()

        task_run.result = result = TaskResult.FAILURE.value
        task_run.error_details = str(traceback.format_exc())

        logger.error(
            "Failed to execute task '%s', with id %d. Exception: %s",
            task_identifier,
            task.pk,
            err_msg,
            exc_info=True,
        )

    labels = {
        "task_identifier": task_identifier,
        "task_type": get_task(task_identifier).task_type.value.lower(),
        "result": result.lower(),
    }

    timer.labels(**labels)  # type: ignore[no-untyped-call]
    ctx.close()

    metrics.flagsmith_task_processor_finished_tasks_total.labels(**labels).inc()

    return task, task_run
