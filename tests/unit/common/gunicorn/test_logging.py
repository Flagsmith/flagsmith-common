import json
import logging
import os
from datetime import timedelta
from pathlib import Path

import pytest
import structlog
from gunicorn.config import Config  # type: ignore[import-untyped]
from pytest_mock import MockerFixture

from common.core.logging import setup_logging
from common.gunicorn.logging import (
    GunicornJsonCapableLogger,
    PrometheusGunicornLogger,
    make_gunicorn_access_processor,
)
from common.gunicorn.utils import DEFAULT_ACCESS_LOG_FORMAT
from common.test_tools import AssertMetricFixture


@pytest.fixture(autouse=True)
def _reset_logging() -> None:
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    structlog.reset_defaults()


def test_gunicorn_prometheus_gunicorn_logger__access_logged__expected_metrics(
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


def test_gunicorn_json_capable_logger__json_format__access_log_uses_processor_formatter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("LOG_FORMAT", "json")
    setup_logging(log_level="INFO", log_format="json")
    config = Config()
    config.set("accesslog", "-")

    # When
    logger = GunicornJsonCapableLogger(config)

    # Then — error log propagates to root
    assert logger.error_log.handlers == []
    assert logger.error_log.propagate is True

    # And — access log keeps its handler (respecting accesslog destination)
    # but uses the root's ProcessorFormatter for structured JSON output
    assert len(logger.access_log.handlers) == 1
    assert logger.access_log.propagate is False
    root_formatter = logging.getLogger().handlers[0].formatter
    assert logger.access_log.handlers[0].formatter is root_formatter


def test_gunicorn_json_capable_logger__generic_format__access_log_keeps_clf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.delenv("LOG_FORMAT", raising=False)
    config = Config()
    config.set("accesslog", "-")

    # When
    logger = GunicornJsonCapableLogger(config)

    # Then — error log propagates
    assert logger.error_log.handlers == []
    assert logger.error_log.propagate is True

    # And — access log has its own CLF handler, does not propagate
    assert len(logger.access_log.handlers) == 1
    assert logger.access_log.propagate is False


@pytest.mark.freeze_time("2023-12-08T06:05:47+00:00")
def test_gunicorn_json_capable_logger__json_format_file__writes_to_access_log_location(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("LOG_FORMAT", "json")
    access_log_file = tmp_path / "access.log"
    setup_logging(
        log_level="DEBUG",
        log_format="json",
        application_loggers=["gunicorn"],
        extra_foreign_processors=[make_gunicorn_access_processor()],
    )
    config = Config()
    config.set("accesslog", str(access_log_file))
    gunicorn_logger = GunicornJsonCapableLogger(config)

    # When
    gunicorn_logger.access_log.info(
        '%(h)s "%(r)s" %(s)s',
        {
            "h": "10.0.0.1",
            "r": "GET /health HTTP/1.1",
            "s": 200,
            "m": "GET",
            "U": "/health",
            "q": "",
            "a": "curl",
            "M": 5,
            "B": 2,
            "t": "[08/Dec/2023:06:05:47 +0000]",
        },
    )

    # Then — output went to the file, not stdout
    content = access_log_file.read_text()
    assert json.loads(content) == {
        "duration_in_ms": 5,
        "levelname": "INFO",
        "logger_name": "gunicorn.access",
        "message": '10.0.0.1 "GET /health HTTP/1.1" 200',
        "method": "GET",
        "path": "/health",
        "pid": os.getpid(),
        "remote_ip": "10.0.0.1",
        "response_size_in_bytes": 2,
        "status": "200",
        "thread_name": "MainThread",
        "time": "2023-12-08T06:05:47+00:00",
        "timestamp": "2023-12-08T06:05:47Z",
        "user_agent": "curl",
    }


@pytest.mark.freeze_time("2023-12-08T06:05:47+00:00")
def test_gunicorn_access_processor__json_format__extracts_structured_fields(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("LOG_FORMAT", "json")
    setup_logging(
        log_level="DEBUG",
        log_format="json",
        application_loggers=["gunicorn"],
        extra_foreign_processors=[
            make_gunicorn_access_processor(
                [
                    "{origin}i",
                    "{access-control-allow-origin}o",
                    "{flagsmith.route}e",
                    "{x-log-me-status}o",
                    "{x-log-me}i",
                ]
            ),
        ],
    )
    config = Config()
    config.set("accesslog", "-")
    gunicorn_logger = GunicornJsonCapableLogger(config)
    access_logger = gunicorn_logger.access_log

    record_args = {
        "h": "192.168.0.1",
        "l": "-",
        "u": "-",
        "t": "[08/Dec/2023:06:05:47 +0000]",
        "r": "GET /test/42?foo=bar HTTP/1.1",
        "m": "GET",
        "U": "/test/42",
        "q": "foo=bar",
        "s": 200,
        "B": 42,
        "b": "42",
        "f": "-",
        "a": "requests",
        "T": 1,
        "M": 1000,
        "D": 1000000,
        "L": "1.0",
        "p": "<42>",
        "{origin}i": "https://app.flagsmith.com",
        "{access-control-allow-origin}o": "https://app.flagsmith.com",
        "{flagsmith.route}e": "/test/{test_id}",
        "{x-log-me-status}o": "acked",
        "{x-log-me}i": "42",
    }

    # When
    access_logger.info(DEFAULT_ACCESS_LOG_FORMAT, record_args)

    # Then
    output = capsys.readouterr().out.strip()
    parsed = json.loads(output)
    assert parsed == {
        "duration_in_ms": 1000,
        "environ_variables": {"flagsmith.route": "/test/{test_id}"},
        "levelname": "INFO",
        "logger_name": "gunicorn.access",
        "message": (
            '192.168.0.1 - - [08/Dec/2023:06:05:47 +0000] "GET /test/42?foo=bar HTTP/1.1"'
            ' 200 42 "-" "requests" https://app.flagsmith.com https://app.flagsmith.com'
        ),
        "method": "GET",
        "path": "/test/42?foo=bar",
        "pid": os.getpid(),
        "remote_ip": "192.168.0.1",
        "request_headers": {
            "origin": "https://app.flagsmith.com",
            "x-log-me": "42",
        },
        "response_headers": {
            "access-control-allow-origin": "https://app.flagsmith.com",
            "x-log-me-status": "acked",
        },
        "response_size_in_bytes": 42,
        "status": "200",
        "thread_name": "MainThread",
        "time": "2023-12-08T06:05:47+00:00",
        "timestamp": "2023-12-08T06:05:47Z",
        "user_agent": "requests",
    }


def test_gunicorn_json_capable_logger__generic_format__outputs_pure_clf(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.delenv("LOG_FORMAT", raising=False)
    setup_logging(
        log_level="DEBUG",
        log_format="generic",
        application_loggers=["gunicorn"],
    )
    config = Config()
    config.set("accesslog", "-")
    gunicorn_logger = GunicornJsonCapableLogger(config)

    record_args = {
        "h": "192.168.0.1",
        "l": "-",
        "u": "-",
        "t": "[08/Dec/2023:06:05:47 +0000]",
        "r": "GET /api/flags HTTP/1.1",
        "m": "GET",
        "U": "/api/flags",
        "q": "",
        "s": 200,
        "B": 1234,
        "b": "1234",
        "f": "-",
        "a": "python-requests/2.31.0",
        "T": 0,
        "M": 42,
        "D": 42000,
        "L": "0.042",
        "p": "<12345>",
        "{origin}i": "-",
        "{access-control-allow-origin}o": "-",
    }

    # When
    gunicorn_logger.access_log.info(DEFAULT_ACCESS_LOG_FORMAT, record_args)

    # Then — pure CLF, no structlog metadata
    output = capsys.readouterr().out.strip()
    assert output == (
        '192.168.0.1 - - [08/Dec/2023:06:05:47 +0000] "GET /api/flags HTTP/1.1"'
        ' 200 1234 "-" "python-requests/2.31.0" - -'
    )
