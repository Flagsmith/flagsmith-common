import argparse
import inspect
import logging
from contextlib import contextmanager
from typing import Any, Generator

from task_processor.threads import TaskRunnerCoordinator
from task_processor.types import TaskCallable, TaskProcessorConfig

logger = logging.getLogger(__name__)


def get_task_identifier_from_function(
    function: TaskCallable[Any],
    task_name: str | None,
) -> str:
    module = inspect.getmodule(function)
    assert module
    return f"{module.__name__.rsplit('.')[-1]}.{task_name or function.__name__}"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--numthreads",
        type=int,
        help="Number of worker threads to run.",
        default=5,
    )
    parser.add_argument(
        "--sleepintervalms",
        type=int,
        help="Number of millis each worker waits before checking for new tasks",
        default=2000,
    )
    parser.add_argument(
        "--graceperiodms",
        type=int,
        help="Number of millis before running task is considered 'stuck'.",
        default=20000,
    )
    parser.add_argument(
        "--queuepopsize",
        type=int,
        help="Number of tasks each worker will pop from the queue on each cycle.",
        default=10,
    )


@contextmanager
def start_task_processor(
    options: dict[str, Any],
) -> Generator[
    TaskRunnerCoordinator,
    None,
    None,
]:
    config = TaskProcessorConfig(
        num_threads=options["numthreads"],
        sleep_interval_ms=options["sleepintervalms"],
        grace_period_ms=options["graceperiodms"],
        queue_pop_size=options["queuepopsize"],
    )

    logger.debug("Config: %s", config)

    coordinator = TaskRunnerCoordinator(config=config)
    coordinator.start()
    try:
        yield coordinator
    finally:
        coordinator.stop()
