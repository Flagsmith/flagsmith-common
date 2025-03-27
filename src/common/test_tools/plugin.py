from typing import Generator

import prometheus_client
import pytest
from prometheus_client.metrics import MetricWrapperBase

from common.test_tools.types import AssertMetricFixture


def assert_metric_impl() -> Generator[AssertMetricFixture, None, None]:
    registry = prometheus_client.REGISTRY
    collectors = [*registry._collector_to_names]

    # Reset registry state
    for collector in collectors:
        if isinstance(collector, MetricWrapperBase):
            collector.clear()

    def _assert_metric(
        *,
        name: str,
        labels: dict[str, str],
        value: float | int,
    ) -> None:
        metric_value = registry.get_sample_value(name, labels)
        assert metric_value == value, (
            f"Metric {name} not found in registry:\n"
            f"{prometheus_client.generate_latest(registry).decode()}"
        )

    yield _assert_metric


assert_metric = pytest.fixture(assert_metric_impl)
