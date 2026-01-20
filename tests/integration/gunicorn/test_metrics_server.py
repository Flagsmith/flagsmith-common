import socket
import urllib.request

import prometheus_client
import pytest

from common.gunicorn.metrics_server import start_metrics_server
from tests import GetLogsFixture


@pytest.mark.prometheus_multiprocess_mode
def test_start_metrics_server__multiprocess_mode__serves_metrics(
    unused_tcp_port: int,
    test_metric: prometheus_client.Counter,
) -> None:
    # Given
    test_metric.labels(test_name="standalone_server_test").inc()

    # When
    start_metrics_server(port=unused_tcp_port)

    # Then
    with urllib.request.urlopen(
        f"http://localhost:{unused_tcp_port}/metrics"
    ) as response:
        content = response.read().decode()

    assert response.status == 200
    assert "pytest_tests_run_total" in content
    assert 'test_name="standalone_server_test"' in content


def test_start_metrics_server__multiproc_dir_unset__logs_warning_and_skips(
    get_logs: GetLogsFixture,
) -> None:
    # Given
    # PROMETHEUS_MULTIPROC_DIR is not set (default state)

    # When
    start_metrics_server()

    # Then
    logs = get_logs("common.gunicorn.metrics_server")
    assert (
        "WARNING",
        "PROMETHEUS_MULTIPROC_DIR not set, skipping metrics server",
    ) in logs


@pytest.mark.prometheus_multiprocess_mode
def test_start_metrics_server__called_multiple_times__remains_idempotent(
    unused_tcp_port: int,
) -> None:
    # Given
    start_metrics_server(port=unused_tcp_port)

    # When
    start_metrics_server(port=unused_tcp_port)
    start_metrics_server(port=unused_tcp_port)

    # Then
    with urllib.request.urlopen(
        f"http://localhost:{unused_tcp_port}/metrics"
    ) as response:
        assert response.status == 200


@pytest.mark.prometheus_multiprocess_mode
def test_start_metrics_server__port_unavailable__logs_error(
    unused_tcp_port: int,
    get_logs: GetLogsFixture,
) -> None:
    # Given
    # Bind to 0.0.0.0 to match prometheus_client's default address
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("0.0.0.0", unused_tcp_port))
    blocker.listen(1)

    try:
        # When
        start_metrics_server(port=unused_tcp_port)

        # Then
        logs = get_logs("common.gunicorn.metrics_server")
        assert any(
            level == "ERROR" and "Failed to start metrics server" in msg
            for level, msg in logs
        )
    finally:
        blocker.close()
