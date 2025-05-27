import logging
import time
import typing
from datetime import datetime, timedelta
from threading import Thread

from django.conf import settings
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
        """
        Consume and execute tasks from the queue, and run recurring tasks

        This method tries to consume tasks from multiple databases as to ensure
        that any remaining tasks are processed after opting in or out of a
        separate database setup.
        """
        database_is_separate = "task_processor" in settings.TASK_PROCESSOR_DATABASES

        for database in settings.TASK_PROCESSOR_DATABASES:
            try:
                run_tasks(database, self.queue_pop_size)

                # Recurring tasks are only run on one database
                if (database == "default") ^ database_is_separate:
                    run_recurring_tasks(database)
            except Exception as exception:
                # To prevent task threads from dying if they get an error retrieving the tasks from the
                # database this will allow the thread to continue trying to retrieve tasks if it can
                # successfully re-establish a connection to the database.
                exception_repr = f"{exception.__class__.__module__}.{repr(exception)}"
                logger.error(
                    f"Error handling tasks from database '{database}': {exception_repr}",
                    exc_info=exception,
                )

                close_old_connections()

    def stop(self) -> None:
        self._stopped = True
