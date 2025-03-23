import prometheus_client
import pytest

from common.test_tools.types import AssertMetricFixture


@pytest.fixture
def assert_metric() -> AssertMetricFixture:
    def _assert_metric(
        *,
        name: str,
        labels: dict[str, str],
        value: float | int,
    ) -> None:
        registry = prometheus_client.REGISTRY
        metric_value = registry.get_sample_value(name, labels)
        assert metric_value == value, (
            f"Metric {name} not found in registry:\n"
            f"{prometheus_client.generate_latest(registry).decode()}"
        )

    return _assert_metric
