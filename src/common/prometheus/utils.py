import typing

import prometheus_client
from django.conf import settings
from prometheus_client.metrics import MetricWrapperBase
from prometheus_client.multiprocess import MultiProcessCollector

T = typing.TypeVar("T", bound=MetricWrapperBase)


class Histogram(prometheus_client.Histogram):
    DEFAULT_BUCKETS = settings.PROMETHEUS_HISTOGRAM_BUCKETS


def get_registry() -> prometheus_client.CollectorRegistry:
    registry = prometheus_client.CollectorRegistry()
    MultiProcessCollector(registry)  # type: ignore[no-untyped-call]
    return registry
