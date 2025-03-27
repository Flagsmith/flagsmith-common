from dataclasses import dataclass
from typing import Callable, ParamSpec, TypeAlias, TypedDict

TaskParameters = ParamSpec("TaskParameters")

TaskCallable: TypeAlias = Callable[TaskParameters, None]


@dataclass
class TaskProcessorConfig:
    num_threads: int
    sleep_interval_ms: int
    grace_period_ms: int
    queue_pop_size: int


class MonitoringInfo(TypedDict):
    waiting: int
