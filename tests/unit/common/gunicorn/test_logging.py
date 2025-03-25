import logging
import logging.config
import os
from datetime import datetime, timedelta

import pytest
from gunicorn.config import AccessLogFormat, Config  # type: ignore[import-untyped]
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from common.core.logging import JsonFormatter
from common.gunicorn.logging import (
    GunicornAccessLogJsonFormatter,
    GunicornJsonCapableLogger,
    PrometheusGunicornLogger,
)
from common.test_tools import AssertMetricFixture


@pytest.mark.freeze_time("2023-12-08T06:05:47.320000+00:00")
def test_gunicorn_access_log_json_formatter__outputs_expected() -> None:
    # Given
    gunicorn_access_log_json_formatter = GunicornAccessLogJsonFormatter()
    log_record = logging.LogRecord(
        name="gunicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=1,
        msg=AccessLogFormat.default,
        args={
            "a": "requests",
            "b": "-",
            "B": None,
            "D": 1000000,
            "f": "-",
            "h": "192.168.0.1",
            "H": None,
            "l": "-",
            "L": "1.0",
            "m": "GET",
            "M": 1000,
            "p": "<42>",
            "q": "foo=bar",
            "R": "^test/",
            "r": "GET",
            "s": 200,
            "T": 1,
            "t": datetime.fromisoformat("2023-12-08T06:05:47.320000+00:00").strftime(
                "[%d/%b/%Y:%H:%M:%S %z]"
            ),
            "u": "-",
            "U": "/test",
        },
        exc_info=None,
    )
    expected_pid = os.getpid()

    # When
    json_log = gunicorn_access_log_json_formatter.get_json_record(log_record)

    # Then
    assert json_log == {
        "duration_in_ms": 1000,
        "levelname": "INFO",
        "logger_name": "gunicorn.access",
        "message": '192.168.0.1 - - [08/Dec/2023:06:05:47 +0000] "GET" 200 - "-" "requests"',
        "method": "GET",
        "path": "/test?foo=bar",
        "pid": expected_pid,
        "remote_ip": "192.168.0.1",
        "route": "^test/",
        "status": "200",
        "thread_name": "MainThread",
        "time": "2023-12-08T06:05:47+00:00",
        "timestamp": "2023-12-08 06:05:47,319",
        "user_agent": "requests",
    }


def test_gunicorn_prometheus_gunicorn_logger__expected_metrics(
    mocker: MockerFixture,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given
    config = Config()
    logger = PrometheusGunicornLogger(config)

    response_mock = mocker.Mock()
    response_mock.status = b"200 OK"
    response_mock.status_code = 200

    # When
    logger.access(
        response_mock,
        mocker.Mock(),
        {"wsgi.django_route": "^health", "REQUEST_METHOD": "GET"},
        timedelta(milliseconds=101),
    )

    # Then
    assert_metric(
        name="http_server_requests_total",
        value=1.0,
        labels={"method": "GET", "route": "^health", "response_status": "200"},
    )
    assert_metric(
        name="http_server_request_duration_seconds_sum",
        value=0.101,
        labels={"method": "GET", "route": "^health", "response_status": "200"},
    )


def test_gunicorn_json_capable_logger__sets_expected_formatters(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.LOG_FORMAT = "json"
    config = Config()
    config.set("accesslog", "-")

    # When
    logger = GunicornJsonCapableLogger(config)

    # Then
    assert isinstance(
        logger.error_log.handlers[0].formatter,
        JsonFormatter,
    )
    assert isinstance(
        logger.access_log.handlers[0].formatter,
        GunicornAccessLogJsonFormatter,
    )


def test_gunicorn_json_capable_logger__non_existent_setting__not_raises(
    settings: SettingsWrapper,
) -> None:
    # Given
    del settings.LOG_FORMAT
    config = Config()

    # When & Then
    from common.gunicorn.logging import GunicornJsonCapableLogger

    GunicornJsonCapableLogger(config)
