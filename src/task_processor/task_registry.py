import enum
import logging
import typing
from dataclasses import dataclass

from task_processor.exceptions import TaskProcessingError
from task_processor.types import TaskCallable

if typing.TYPE_CHECKING:
    from task_processor.decorators import TaskHandler  # noqa: F401

logger = logging.getLogger(__name__)


class TaskType(enum.Enum):
    STANDARD = "STANDARD"
    RECURRING = "RECURRING"


@dataclass
class RegisteredTask:
    task_identifier: str
    task_callable: TaskCallable[typing.Any]
    task_type: TaskType = TaskType.STANDARD
    task_handler: "TaskHandler[typing.Any] | None" = None
    task_kwargs: dict[str, typing.Any] | None = None


registered_tasks: dict[str, RegisteredTask] = {}


def initialise() -> None:
    global registered_tasks

    from task_processor.models import RecurringTask

    for task_identifier, registered_task in registered_tasks.items():
        logger.debug("Initialising task '%s'", task_identifier)

        if registered_task.task_type == TaskType.RECURRING:
            logger.debug("Persisting recurring task '%s'", task_identifier)
            RecurringTask.objects.update_or_create(
                task_identifier=task_identifier,
                defaults=registered_task.task_kwargs,
            )


def get_task(task_identifier: str) -> RegisteredTask:
    global registered_tasks

    try:
        return registered_tasks[task_identifier]
    except KeyError:
        raise TaskProcessingError(
            "No task registered with identifier '%s'. Ensure your task is "
            "decorated with @register_task_handler.",
            task_identifier,
        )


def register_task(
    task_identifier: str,
    task_handler: "TaskHandler[typing.Any]",
) -> None:
    global registered_tasks

    registered_task = RegisteredTask(
        task_identifier=task_identifier,
        task_handler=task_handler,
        task_callable=task_handler.unwrapped,
    )
    registered_tasks[task_identifier] = registered_task


def register_recurring_task(
    task_identifier: str,
    task_callable: TaskCallable[typing.Any],
    **task_kwargs: typing.Any,
) -> None:
    global registered_tasks

    logger.debug("Registering recurring task '%s'", task_identifier)

    registered_task = RegisteredTask(
        task_identifier=task_identifier,
        task_callable=task_callable,
        task_type=TaskType.RECURRING,
        task_kwargs=task_kwargs,
    )
    registered_tasks[task_identifier] = registered_task

    logger.debug(
        "Registered tasks now has the following tasks registered: %s",
        list(registered_tasks.keys()),
    )
