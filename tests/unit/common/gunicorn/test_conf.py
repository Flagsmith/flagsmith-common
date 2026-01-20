from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from common.gunicorn.conf import child_exit, when_ready


def test_child_exit__calls_mark_process_dead_with_worker_pid(
    mocker: MockerFixture,
) -> None:
    # Given
    mark_process_dead_mock = mocker.patch("common.gunicorn.conf.mark_process_dead")
    server = Mock()
    worker = Mock()
    worker.pid = 12345

    # When
    child_exit(server, worker)

    # Then
    mark_process_dead_mock.assert_called_once_with(12345)


@pytest.mark.parametrize("prometheus_enabled", ("true", "TRUE"))
def test_when_ready__prometheus_enabled__starts_metrics_server(
    mocker: MockerFixture,
    prometheus_enabled: str,
) -> None:
    # Given
    mocker.patch.dict("os.environ", {"PROMETHEUS_ENABLED": prometheus_enabled})
    start_metrics_server_mock = mocker.patch(
        "common.gunicorn.metrics_server.start_metrics_server"
    )
    server = Mock()

    # When
    when_ready(server)

    # Then
    start_metrics_server_mock.assert_called_once()


@pytest.mark.parametrize("prometheus_enabled", ("", "false"))
def test_when_ready__prometheus_disabled__does_not_start_metrics_server(
    mocker: MockerFixture,
    prometheus_enabled: str,
) -> None:
    # Given
    mocker.patch.dict("os.environ", {"PROMETHEUS_ENABLED": prometheus_enabled})
    start_metrics_server_mock = mocker.patch(
        "common.gunicorn.metrics_server.start_metrics_server"
    )
    server = Mock()

    # When
    when_ready(server)

    # Then
    start_metrics_server_mock.assert_not_called()
