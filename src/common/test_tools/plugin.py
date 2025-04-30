from typing import Generator

import prometheus_client
import pytest
from prometheus_client.metrics import MetricWrapperBase
from pyfakefs.fake_filesystem import FakeFilesystem

from common.test_tools.types import AssertMetricFixture, Snapshot, SnapshotFixture


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("snapshot")
    group.addoption(
        "--snapshot-update",
        action="store_true",
        help="Update snapshot files instead of testing against them.",
    )


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


@pytest.fixture
def snapshot(request: pytest.FixtureRequest) -> SnapshotFixture:
    """
    Retrieve a `Snapshot` object getter for the current test.
    The snapshot is stored in the `snapshots` directory next to the test file.

    Snapshot files are named after the test function name (+ ".txt") by default.
    If a name is provided to the getter, the snapshot will be stored in a file with that name.
    The name is relative to the `snapshots` directory.

    When `--snapshot-update` is provided to `pytest`:
    - The snapshot will be created if it does not exist.
    - If the comparison is false, the snapshot will be updated with the string it's being compared to in the test,
    and the test will be marked as expected to fail.
    """
    for_update = request.config.getoption("--snapshot-update")
    snapshot_dir = request.path.parent / "snapshots"
    snapshot_dir.mkdir(exist_ok=True)

    def _get_snapshot(name: str = "") -> Snapshot:
        snapshot_name = name or f"{request.node.name}.txt"
        snapshot_path = snapshot_dir / snapshot_name
        return Snapshot(snapshot_path, for_update=for_update)

    return _get_snapshot
