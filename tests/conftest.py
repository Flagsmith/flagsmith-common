import os
from importlib import reload

import prometheus_client
import prometheus_client.values
import pytest

pytest_plugins = "flagsmith-test-tools"


@pytest.fixture(scope="session")
def prometheus_multiproc_dir(tmp_path_factory: pytest.TempPathFactory) -> str:
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = prometheus_multiproc_dir_path = str(
        tmp_path_factory.mktemp("prometheus_multiproc")
    )
    reload(prometheus_client.values)
    return prometheus_multiproc_dir_path


@pytest.fixture(scope="session")
def test_metric(prometheus_multiproc_dir: str) -> prometheus_client.Counter:
    return prometheus_client.Counter(
        "pytest_tests_run_total",
        "Total number of tests run by pytest",
        ["test_name"],
    )
