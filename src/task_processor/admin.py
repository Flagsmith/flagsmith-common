from datetime import datetime

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from task_processor.models import RecurringTask


@admin.register(RecurringTask)
class RecurringTaskAdmin(admin.ModelAdmin[RecurringTask]):
    list_display = (
        "uuid",
        "task_identifier",
        "run_every",
        "last_run_status",
        "last_run_finished_at",
        "is_locked",
    )
    readonly_fields = ("args", "kwargs")

    def last_run_status(self, instance: RecurringTask) -> str | None:
        if last_run := instance.task_runs.order_by("-started_at").first():
            return last_run.result
        return None

    def last_run_finished_at(self, instance: RecurringTask) -> datetime | None:
        if last_run := instance.task_runs.order_by("-started_at").first():
            return last_run.finished_at
        return None

    @admin.action(description="Unlock selected tasks")
    def unlock(
        self,
        request: HttpRequest,
        queryset: QuerySet[RecurringTask],
    ) -> None:
        queryset.update(is_locked=False)
