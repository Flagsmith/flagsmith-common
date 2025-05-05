import typing

from django.conf import settings
from django.db import connections, transaction
from django.db.models import Manager
from django.db.utils import ProgrammingError
from django.utils.connection import ConnectionDoesNotExist

if typing.TYPE_CHECKING:
    from django.db.models.query import RawQuerySet

    from task_processor.models import RecurringTask, Task


class TaskManager(Manager["Task"]):
    def get_tasks_to_process(  # noqa: C901
        self,
        num_tasks: int,
        skip_old_database: bool = False,
    ) -> typing.Generator["Task", None, None]:
        """
        Retrieve tasks to process from the database

        This does its best effort to retrieve tasks from the old database first
        """
        if not skip_old_database:
            old_database = "default" if self._is_database_separate else "task_processor"
            old_tasks = self._fetch_tasks_from(old_database, num_tasks)

            # Fetch tasks from the previous database
            try:
                with transaction.atomic(using=old_database):
                    first_task = next(old_tasks)
            except StopIteration:
                pass  # Empty set
            except ProgrammingError:
                pass  # Function no longer exists in old database
            except ConnectionDoesNotExist:
                pass  # Database not available
            else:
                yield first_task
                num_tasks -= 1
                for task in old_tasks:
                    yield task
                    num_tasks -= 1

            if num_tasks == 0:
                return

        new_database = "task_processor" if self._is_database_separate else "default"
        new_tasks = self._fetch_tasks_from(new_database, num_tasks)

        # Fetch tasks from the new database
        try:
            with transaction.atomic(using=new_database):
                first_task = next(new_tasks)
        except StopIteration:
            pass  # Empty set
        except ProgrammingError:
            # Function doesn't exist in the database yet
            self._create_or_replace_function__get_tasks_to_process()
            yield from self.get_tasks_to_process(num_tasks, skip_old_database=True)
        else:
            yield first_task
            yield from new_tasks

    @property
    def _is_database_separate(self) -> bool:
        """
        Check whether the task processor database is separate from the default database
        """
        return "task_processor" in settings.DATABASES

    def _fetch_tasks_from(
        self, database: str, num_tasks: int
    ) -> typing.Iterator["Task"]:
        """
        Retrieve tasks from the specified Django database
        """
        return (
            self.using(database)
            .raw("SELECT * FROM get_tasks_to_process(%s)", [num_tasks])
            .iterator()
        )

    def _create_or_replace_function__get_tasks_to_process(self) -> None:
        """
        Create or replace the function to get tasks to process.
        """
        database = "task_processor" if self._is_database_separate else "default"
        with connections[database].cursor() as cursor:
            cursor.execute(
                """
                CREATE OR REPLACE FUNCTION get_tasks_to_process(num_tasks integer)
                RETURNS SETOF task_processor_task AS $$
                DECLARE
                    row_to_return task_processor_task;
                BEGIN
                    -- Select the tasks that needs to be processed
                    FOR row_to_return IN
                        SELECT *
                        FROM task_processor_task
                        WHERE num_failures < 3 AND scheduled_for < NOW() AND completed = FALSE AND is_locked = FALSE
                        ORDER BY priority ASC, scheduled_for ASC, created_at ASC
                        LIMIT num_tasks
                        -- Select for update to ensure that no other workers can select these tasks while in this transaction block
                        FOR UPDATE SKIP LOCKED
                    LOOP
                        -- Lock every selected task(by updating `is_locked` to true)
                        UPDATE task_processor_task
                        -- Lock this row by setting is_locked True, so that no other workers can select these tasks after this
                        -- transaction is complete (but the tasks are still being executed by the current worker)
                        SET is_locked = TRUE
                        WHERE id = row_to_return.id;
                        -- If we don't explicitly update the `is_locked` column here, the client will receive the row that is actually locked but has the `is_locked` value set to `False`.
                        row_to_return.is_locked := TRUE;
                        RETURN NEXT row_to_return;
                    END LOOP;

                    RETURN;
                END;
                $$ LANGUAGE plpgsql
                """
            )


class RecurringTaskManager(Manager["RecurringTask"]):
    def get_tasks_to_process(self) -> "RawQuerySet[RecurringTask]":
        return self.raw("SELECT * FROM get_recurringtasks_to_process()")
