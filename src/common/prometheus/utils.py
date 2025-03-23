import typing

import prometheus_client
from prometheus_client.metrics import MetricWrapperBase
from prometheus_client.multiprocess import MultiProcessCollector

from common.prometheus.constants import UNKNOWN_LABEL_VALUE
from common.prometheus.types import LabelValue

T = typing.TypeVar("T", bound=MetricWrapperBase)


def get_registry() -> prometheus_client.CollectorRegistry:
    registry = prometheus_client.CollectorRegistry()
    MultiProcessCollector(registry)  # type: ignore[no-untyped-call]
    return registry


def with_labels(
    metric: T,
    **labels: LabelValue | None,
) -> T:
    """
    Add labels to a given metric. If a label value is `None` or is not provided,
    replace with the `UNKNOWN_LABEL_VALUE` constant.
    """
    return metric.labels(
        **{
            **{key: UNKNOWN_LABEL_VALUE for key in metric._labelnames},
            **{key: value for key, value in labels.items() if value is not None},
        },
    )
