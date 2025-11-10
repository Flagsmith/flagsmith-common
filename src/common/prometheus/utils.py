import importlib
import os
import pathlib
import shutil
from tempfile import gettempdir

import prometheus_client
from django.conf import settings
from prometheus_client.metrics import MetricWrapperBase
from prometheus_client.multiprocess import MultiProcessCollector

from common.core.constants import DEFAULT_PROMETHEUS_MULTIPROC_DIR_NAME


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


def prepare_prom_multiproc_dir() -> None:
    prom_dir = pathlib.Path(
        os.environ.setdefault(
            "PROMETHEUS_MULTIPROC_DIR",
            os.path.join(gettempdir(), DEFAULT_PROMETHEUS_MULTIPROC_DIR_NAME),
        )
    )

    if prom_dir.exists():
        for p in prom_dir.rglob("*"):
            try:
                # Ensure that the cleanup doesn't silently fail on
                # files and subdirs created by other users.
                p.chmod(0o777)
            except Exception:  # pragma: no cover
                pass

        shutil.rmtree(prom_dir, ignore_errors=True)

    prom_dir.mkdir(parents=True, exist_ok=True)

    # While `mkdir` sets mode=0o777 by default, this can be affected by umask resulting in
    # lesser permissions for other users. This step ensures the directory is writable for
    # all users.
    prom_dir.chmod(0o777)
