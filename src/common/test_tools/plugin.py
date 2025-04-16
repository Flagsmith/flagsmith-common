from typing import Generator

import prometheus_client
import pytest
from prometheus_client.metrics import MetricWrapperBase
from pyfakefs.fake_filesystem import FakeFilesystem

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


@pytest.fixture()
def saas_mode(fs: FakeFilesystem) -> Generator[None, None, None]:
    from common.core.utils import is_saas

    is_saas.cache_clear()
    fs.create_file("./SAAS_DEPLOYMENT")

    yield

    is_saas.cache_clear()


@pytest.fixture()
def enterprise_mode(fs: FakeFilesystem) -> Generator[None, None, None]:
    from common.core.utils import is_enterprise

    is_enterprise.cache_clear()
    fs.create_file("./ENTERPRISE_VERSION")

    yield

    is_enterprise.cache_clear()


@pytest.fixture(autouse=True)
def flagsmith_markers_marked(
    request: pytest.FixtureRequest,
) -> None:
    for marker in request.node.iter_markers():
        if marker.name == "saas_mode":
            request.getfixturevalue("saas_mode")
        if marker.name == "enterprise_mode":
            request.getfixturevalue("enterprise_mode")
