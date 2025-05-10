import typing

from django.db.models import Manager

if typing.TYPE_CHECKING:
    from task_processor.models import RecurringTask, Task


class TaskManager(Manager["Task"]):
    def get_tasks_to_process(self, num_tasks: int) -> typing.List["Task"]:
        return list(
            self.raw(
                "SELECT * FROM get_tasks_to_process(%s)",
                [num_tasks],
            ),
        )


class RecurringTaskManager(Manager["RecurringTask"]):
    def get_tasks_to_process(self) -> typing.List["RecurringTask"]:
        return list(
            self.raw("SELECT * FROM get_recurringtasks_to_process()"),
        )
