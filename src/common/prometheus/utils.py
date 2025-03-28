import importlib

import prometheus_client
from django.conf import settings
from prometheus_client.metrics import MetricWrapperBase
from prometheus_client.multiprocess import MultiProcessCollector


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

    registry = prometheus_client.REGISTRY

    for module_name in metric_module_names:
        metrics_module = importlib.import_module(module_name)

        for module_attr in vars(metrics_module).values():
            if isinstance(module_attr, MetricWrapperBase):
                # Unregister the collector from the registry
                registry.unregister(module_attr)

        importlib.reload(metrics_module)
