import logging
import time
import typing
from datetime import datetime, timedelta
from threading import Thread

from django.db import close_old_connections
from django.utils import timezone

from task_processor.processor import run_recurring_tasks, run_tasks
from task_processor.task_registry import initialise
from task_processor.types import TaskProcessorConfig

logger = logging.getLogger(__name__)


class TaskRunnerCoordinator(Thread):
    def __init__(
        self,
        *args: typing.Any,
        config: TaskProcessorConfig,
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.config = config
        self._threads: list[TaskRunner] = []
        self._monitor_threads = True

    def run(self) -> None:
        initialise()

        logger.info("Processor starting")

        for _ in range(self.config.num_threads):
            self._threads.append(
                task := TaskRunner(
                    sleep_interval_millis=self.config.sleep_interval_ms,
                    queue_pop_size=self.config.queue_pop_size,
                )
            )
            task.start()

        ms_before_unhealthy = (
            self.config.grace_period_ms + self.config.sleep_interval_ms
        )
        while self._monitor_threads:
            time.sleep(1)
            unhealthy_threads = self._get_unhealthy_threads(
                ms_before_unhealthy=ms_before_unhealthy
            )
            if unhealthy_threads:
                logger.warning("%d unhealthy threads detected", len(unhealthy_threads))

        for thread in self._threads:
            thread.join()

    def _get_unhealthy_threads(self, ms_before_unhealthy: int) -> list["TaskRunner"]:
        unhealthy_threads = []
        healthy_threshold = timezone.now() - timedelta(milliseconds=ms_before_unhealthy)

        for thread in self._threads:
            if (
                not thread.is_alive()
                or not thread.last_checked_for_tasks
                or thread.last_checked_for_tasks < healthy_threshold
            ):
                unhealthy_threads.append(thread)
        return unhealthy_threads

    def stop(self) -> None:
        self._monitor_threads = False
        for t in self._threads:
            t.stop()


class TaskRunner(Thread):
    def __init__(
        self,
        *args: typing.Any,
        sleep_interval_millis: int = 2000,
        queue_pop_size: int = 1,
        **kwargs: typing.Any,
    ):
        super(TaskRunner, self).__init__(*args, **kwargs)
        self.sleep_interval_millis = sleep_interval_millis
        self.queue_pop_size = queue_pop_size
        self.last_checked_for_tasks: datetime | None = None

        self._stopped = False

    def run(self) -> None:
        while not self._stopped:
            self.last_checked_for_tasks = timezone.now()
            self.run_iteration()
            time.sleep(self.sleep_interval_millis / 1000)

    def run_iteration(self) -> None:
        try:
            run_tasks(self.queue_pop_size)
            run_recurring_tasks()
        except Exception as e:
            # To prevent task threads from dying if they get an error retrieving the tasks from the
            # database this will allow the thread to continue trying to retrieve tasks if it can
            # successfully re-establish a connection to the database.
            # TODO: is this also what is causing tasks to get stuck as locked? Can we unlock
            #  tasks here?

            logger.error("Received error retrieving tasks: %s.", e, exc_info=e)
            close_old_connections()

    def stop(self) -> None:
        self._stopped = True
