import typing

from django.db.models import Manager

if typing.TYPE_CHECKING:
    from django.db.models.query import RawQuerySet

    from task_processor.models import RecurringTask, Task


class TaskManager(Manager["Task"]):
    def get_tasks_to_process(self, num_tasks: int) -> "RawQuerySet[Task]":
        return self.raw("SELECT * FROM get_tasks_to_process(%s)", [num_tasks])


class RecurringTaskManager(Manager["RecurringTask"]):
    def get_tasks_to_process(self) -> "RawQuerySet[RecurringTask]":
        return self.raw("SELECT * FROM get_recurringtasks_to_process()")
