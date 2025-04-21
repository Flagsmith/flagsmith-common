import logging
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
def test_gunicorn_access_log_json_formatter__outputs_expected(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.ACCESS_LOG_JSON_EXTRA_ITEMS = [
        "{flagsmith.route}e",
        "{X-LOG-ME-STATUS}o",
        "{x-log-me}i",
    ]

    gunicorn_access_log_json_formatter = GunicornAccessLogJsonFormatter()
    log_record = logging.LogRecord(
        name="gunicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=1,
        msg=AccessLogFormat.default,
        args={
            "{flagsmith.route}e": "/test/{test_id}",
            "{wsgi.version}e": (1, 0),
            "{x-log-me-status}o": "acked",
            "{x-log-me}i": "42",
            "a": "requests",
            "b": 42,
            "B": 42,
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
            "r": "GET",
            "s": 200,
            "T": 1,
            "t": datetime.fromisoformat("2023-12-08T06:05:47.320000+00:00").strftime(
                "[%d/%b/%Y:%H:%M:%S %z]"
            ),
            "u": "-",
            "U": "/test/42",
        },
        exc_info=None,
    )
    expected_pid = os.getpid()

    # When
    json_log = gunicorn_access_log_json_formatter.get_json_record(log_record)

    # Then
    assert json_log == {
        "duration_in_ms": 1000,
        "environ_variables": {
            "flagsmith.route": "/test/{test_id}",
        },
        "levelname": "INFO",
        "logger_name": "gunicorn.access",
        "message": '192.168.0.1 - - [08/Dec/2023:06:05:47 +0000] "GET" 200 42 "-" "requests"',
        "method": "GET",
        "path": "/test/42?foo=bar",
        "pid": expected_pid,
        "remote_ip": "192.168.0.1",
        "request_headers": {
            "x-log-me": "42",
        },
        "response_headers": {
            "x-log-me-status": "acked",
        },
        "response_size_in_bytes": 42,
        "route": "/test/{test_id}",
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
    response_mock.sent = 42

    # When
    logger.access(
        response_mock,
        mocker.Mock(),
        {"flagsmith.route": "/health", "REQUEST_METHOD": "GET"},
        timedelta(milliseconds=101),
    )

    # Then
    assert_metric(
        name="flagsmith_http_server_requests_total",
        value=1.0,
        labels={"method": "GET", "route": "/health", "response_status": "200"},
    )
    assert_metric(
        name="flagsmith_http_server_request_duration_seconds_sum",
        value=0.101,
        labels={"method": "GET", "route": "/health", "response_status": "200"},
    )
    assert_metric(
        name="flagsmith_http_server_response_size_bytes_sum",
        value=42.0,
        labels={"method": "GET", "route": "/health", "response_status": "200"},
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
