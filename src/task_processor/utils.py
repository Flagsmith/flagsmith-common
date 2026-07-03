import argparse
import inspect
import logging
import os
from contextlib import contextmanager
from typing import Any, Generator

from environs import Env

from task_processor.constants import (
    DEFAULT_TASK_PROCESSOR_GRACE_PERIOD_MS,
    DEFAULT_TASK_PROCESSOR_NUM_THREADS,
    DEFAULT_TASK_PROCESSOR_QUEUE_POP_SIZE,
    DEFAULT_TASK_PROCESSOR_SLEEP_INTERVAL_MS,
)
from task_processor.threads import TaskRunnerCoordinator
from task_processor.types import TaskCallable, TaskProcessorConfig

logger = logging.getLogger(__name__)

env = Env()


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
        default=env.int(
            "TASK_PROCESSOR_NUM_THREADS",
            default=DEFAULT_TASK_PROCESSOR_NUM_THREADS,
        ),
    )
    parser.add_argument(
        "--sleepintervalms",
        type=int,
        help="Number of millis each worker waits before checking for new tasks",
        default=(
            env.int("TASK_PROCESSOR_SLEEP_INTERVAL_MS")
            if "TASK_PROCESSOR_SLEEP_INTERVAL_MS" in os.environ
            else env.int(
                "TASK_PROCESSOR_SLEEP_INTERVAL",
                default=DEFAULT_TASK_PROCESSOR_SLEEP_INTERVAL_MS,
            )
        ),
    )
    parser.add_argument(
        "--graceperiodms",
        type=int,
        help="Number of millis before running task is considered 'stuck'.",
        default=env.int(
            "TASK_PROCESSOR_GRACE_PERIOD_MS",
            default=DEFAULT_TASK_PROCESSOR_GRACE_PERIOD_MS,
        ),
    )
    parser.add_argument(
        "--queuepopsize",
        type=int,
        help="Number of tasks each worker will pop from the queue on each cycle.",
        default=env.int(
            "TASK_PROCESSOR_QUEUE_POP_SIZE",
            default=DEFAULT_TASK_PROCESSOR_QUEUE_POP_SIZE,
        ),
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
