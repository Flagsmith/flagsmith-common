import prometheus_client
from django.conf import settings

from common.prometheus import Histogram

flagsmith_task_processor_enqueued_tasks_total = prometheus_client.Counter(
    "flagsmith_task_processor_enqueued_tasks_total",
    "Total number of enqueued tasks",
    ["task_identifier"],
)

if settings.TASK_PROCESSOR_MODE:
    flagsmith_task_processor_finished_tasks_total = prometheus_client.Counter(
        "flagsmith_task_processor_finished_tasks_total",
        "Total number of finished tasks",
        ["task_identifier", "result"],
    )
    flagsmith_task_processor_task_duration_seconds = Histogram(
        "flagsmith_task_processor_task_duration_seconds",
        "Task processor task duration in seconds",
        ["task_identifier", "result"],
    )
