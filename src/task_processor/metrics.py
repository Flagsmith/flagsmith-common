import prometheus_client

from common.prometheus import Histogram

task_processor_task_duration_seconds = Histogram(
    "task_processor_task_duration_seconds",
    "Task processor task duration in seconds",
    ["task_identifier"],
)
task_processor_queued_tasks_total = prometheus_client.Counter(
    "task_processor_queued_tasks_total",
    "Total number of queued tasks",
    ["task_identifier"],
)
task_processor_finished_tasks_total = prometheus_client.Counter(
    "task_processor_finished_tasks_total",
    "Total number of finished tasks",
    ["task_identifier", "status"],
)
