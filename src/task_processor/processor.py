import logging
import traceback
import typing
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import timedelta
from importlib.metadata import version

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone
from opentelemetry import context as otel_context
from opentelemetry import propagate, trace

from task_processor import metrics
from task_processor.exceptions import TaskBackoffError
from task_processor.managers import RecurringTaskManager, TaskManager
from task_processor.models import (
    AbstractBaseTask,
    RecurringTask,
    RecurringTaskRun,
    Task,
    TaskResult,
    TaskRun,
)
from task_processor.task_registry import TaskType, get_task

T = typing.TypeVar("T", bound=AbstractBaseTask)
AnyTaskRun = TaskRun | RecurringTaskRun

logger = logging.getLogger(__name__)

UNREGISTERED_RECURRING_TASK_GRACE_PERIOD = timedelta(minutes=30)


def run_tasks(database: str, num_tasks: int = 1) -> list[TaskRun]:
    if num_tasks < 1:
        raise ValueError("Number of tasks to process must be at least one")

    task_manager: TaskManager = Task.objects.db_manager(database)
    tasks = task_manager.get_tasks_to_process(num_tasks)
    if tasks:
        logger.debug(f"Running {len(tasks)} task(s) from database '{database}'")

        executed_tasks = []
        task_runs = []

        for task in tasks:
            task, task_run = _run_task(task)

            executed_tasks.append(task)
            assert isinstance(task_run, TaskRun)
            task_runs.append(task_run)

        if executed_tasks:
            Task.objects.using(database).bulk_update(
                executed_tasks,
                fields=["completed", "num_failures", "is_locked", "scheduled_for"],
            )

        if task_runs:
            TaskRun.objects.using(database).bulk_create(task_runs)
            logger.debug(
                f"Finished running {len(task_runs)} task(s) from database '{database}'"
            )

        return task_runs

    return []


def run_recurring_task(database: str) -> RecurringTaskRun | None:
    # NOTE: We will probably see a lot of delay in the execution of recurring tasks
    # if the tasks take longer then `run_every` to execute. This is not
    # a problem for now, but we should be mindful of this limitation
    task_manager: RecurringTaskManager = RecurringTask.objects.db_manager(database)
    task = task_manager.get_task_to_process()
    if task is None:
        return None

    logger.debug(f"Running recurring task '{task.task_identifier}'")

    if not task.is_task_registered:
        # This is necessary to ensure that old instances of the task processor,
        # which may still be running during deployment, do not remove tasks added by new instances.
        # Reference: https://github.com/Flagsmith/flagsmith/issues/2551
        task_age = timezone.now() - task.created_at
        if task_age > UNREGISTERED_RECURRING_TASK_GRACE_PERIOD:
            task.delete(using=database)
        return None

    task_run: RecurringTaskRun | None = None
    if task.should_execute:
        # Persist the task run before execution so that, if the worker is
        # killed mid-task, we still have a row we can later mark as timed
        # out when the task is unlocked by the timeout-based reaper in
        # `get_recurringtasks_to_process`.
        task_run = RecurringTaskRun(started_at=timezone.now(), task=task)
        task_run.save(using=database)
        task, run = _run_task(task, task_run=task_run)
        assert run is task_run
        # task.run() may have idled the DB connection past the server's
        # session timeout; drop stale connections so the saves below open
        # a fresh one. See Sentry FLAGSMITH-API-5EM.
        close_old_connections()
    else:
        task.unlock()

    task.save(using=database, update_fields=["is_locked", "locked_at"])

    if task_run:
        task_run.save(
            using=database,
            update_fields=["finished_at", "result", "error_details"],
        )
        logger.debug(f"Finished running recurring task '{task.task_identifier}'")
        return task_run

    return None


def _run_task(
    task: T,
    task_run: AnyTaskRun | None = None,
) -> typing.Tuple[T, AnyTaskRun]:
    assert settings.TASK_PROCESSOR_MODE, (
        "Attempt to run tasks in a non-task-processor environment"
    )

    ctx = ExitStack()
    timer = metrics.flagsmith_task_processor_task_duration_seconds.time()
    ctx.enter_context(timer)

    task_identifier = task.task_identifier
    registered_task = get_task(task_identifier)

    logger.debug(
        f"Running task {task_identifier} id={task.pk} args={task.args} kwargs={task.kwargs}"
    )
    if task_run is None:
        task_run = task.task_runs.model(started_at=timezone.now(), task=task)  # type: ignore[attr-defined]
    result: str
    executor = None

    extracted_ctx = propagate.extract(task.trace_context or {})
    tracer = trace.get_tracer("task_processor", version("flagsmith-common"))
    span = tracer.start_span(task_identifier, context=extracted_ctx)
    otel_token = otel_context.attach(trace.set_span_in_context(span, extracted_ctx))

    try:
        # Use explicit executor management to avoid blocking on shutdown
        # when tasks timeout but continue running in worker threads.
        # The default context manager behavior (wait=True) would block
        # the TaskRunner thread indefinitely waiting for stuck workers.
        executor = ThreadPoolExecutor(max_workers=1)
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

        span.set_status(trace.StatusCode.ERROR, err_msg)
        span.record_exception(e)

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

        if isinstance(e, TaskBackoffError):
            assert registered_task.task_type == TaskType.STANDARD, (
                "Attempt to back off a recurring task (currently not supported)"
            )
            if typing.TYPE_CHECKING:
                assert isinstance(task, Task)
            if task.num_failures <= 3:
                delay_until = e.delay_until or timezone.now() + timedelta(
                    seconds=settings.TASK_BACKOFF_DEFAULT_DELAY_SECONDS,
                )
                task.scheduled_for = delay_until
                logger.info(
                    "Backoff requested. Task '%s' set to retry at %s",
                    task_identifier,
                    delay_until,
                )

    finally:
        # Always shutdown the executor without waiting for worker threads.
        # This prevents the TaskRunner thread from blocking indefinitely
        # when a task times out but continues running in a worker thread.
        if executor is not None:
            executor.shutdown(wait=False)

    labels = {
        "task_identifier": task_identifier,
        "task_type": registered_task.task_type.value.lower(),
        "result": result.lower(),
    }

    timer.labels(**labels)  # type: ignore[no-untyped-call]
    ctx.close()

    metrics.flagsmith_task_processor_finished_tasks_total.labels(**labels).inc()

    span.set_attributes(labels)
    span.end()
    otel_context.detach(otel_token)

    return task, task_run
