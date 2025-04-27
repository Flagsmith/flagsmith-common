import os
from importlib import reload
from typing import Generator

import prometheus_client
import pytest

pytest_plugins = "flagsmith-test-tools"


@pytest.fixture()
def prometheus_multiproc_dir(
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[str, None, None]:
    """
    This fixture makes `prometheus_client.multiprocess.MultiProcessCollector` work in pytest.
    It's not required by general metric-related tests, just the ones that invoke
    logic that relies directly on `prometheus_client.multiprocess.MultiProcessCollector`.
    """
    # Set the environment variable expected by prometheus_client
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = prometheus_multiproc_dir_path = str(
        tmp_path_factory.mktemp("prometheus_multiproc")
    )
    # This effectively installs multiprocess mode,
    # forcing metrics to be written to the file system
    # and picked up by `MultiProcessCollector`
    reload(prometheus_client.values)

    yield prometheus_multiproc_dir_path

    # Clean up the environment variable after the test
    # to avoid side effects on other tests
    del os.environ["PROMETHEUS_MULTIPROC_DIR"]
    # Reinstall the default mode
    reload(prometheus_client.values)


@pytest.fixture(autouse=True)
def prometheus_multiprocess_mode_marked(request: pytest.FixtureRequest) -> None:
    for marker in request.node.iter_markers():
        if marker.name == "prometheus_multiprocess_mode":
            request.getfixturevalue("prometheus_multiproc_dir")
            return


@pytest.fixture(scope="session")
def test_metric() -> prometheus_client.Counter:
    return prometheus_client.Counter(
        "pytest_tests_run_total",
        "Total number of tests run by pytest",
        ["test_name"],
    )
