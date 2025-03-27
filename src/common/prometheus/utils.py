import importlib
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


def reload_metrics(*metric_module_names: str) -> None:
    """
    Clear the registry of all collectors from the given modules
    and reload the modules to register the collectors again.

    Used in tests to reset the state of the metrics module
    when needed.
    """

    for module_name in metric_module_names:
        metrics_module = importlib.import_module(module_name)

        _collectors = metrics_module.__dict__.values()

        for collector in [
            *(registry := prometheus_client.REGISTRY)._collector_to_names
        ]:
            if collector in _collectors:
                registry.unregister(collector)

        importlib.reload(metrics_module)
