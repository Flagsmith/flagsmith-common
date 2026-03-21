import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Generator
from unittest.mock import patch

import pytest
import sentry_sdk
import structlog
from sentry_sdk.envelope import Envelope
from sentry_sdk.transport import Transport

from common.core.logging import JsonFormatter, setup_logging

if TYPE_CHECKING:
    from sentry_sdk._types import Event


@pytest.fixture(autouse=True)
def reset_logging() -> None:
    """Reset logging and structlog state before each test."""
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    structlog.reset_defaults()


@pytest.fixture
def test_app_loggers() -> list[str]:
    return ["test"]


class MockSentryTransport(Transport):
    def __init__(self) -> None:
        self.events: list[Event] = []

    def capture_envelope(self, envelope: Envelope) -> None:
        if event := envelope.get_event():
            self.events.append(event)


@pytest.fixture
def sentry_transport_mock() -> Generator[MockSentryTransport, None, None]:
    transport = MockSentryTransport()
    sentry_sdk.init(transport=transport, transport_queue_size=0)
    yield transport
    sentry_sdk.flush()
    sentry_sdk.init(transport=None)


@pytest.mark.freeze_time("2023-12-08T06:05:47+00:00")
def test_json_formatter__format_log__outputs_expected(
    caplog: pytest.LogCaptureFixture,
    request: pytest.FixtureRequest,
) -> None:
    # Given
    json_formatter = JsonFormatter()

    caplog.handler.setFormatter(json_formatter)
    logger = logging.getLogger("test_json_formatter__outputs_expected")
    logger.setLevel(logging.INFO)

    expected_pid = os.getpid()
    expected_module_path = os.path.abspath(request.path)

    def _log_traceback() -> None:
        try:
            raise Exception()
        except Exception as exc:
            logger.error("this is an error", exc_info=exc)

    expected_lineno = _log_traceback.__code__.co_firstlineno + 2
    expected_tb_string = (
        "Traceback (most recent call last):\n"
        f'  File "{expected_module_path}",'
        f" line {expected_lineno}, in _log_traceback\n"
        "    raise Exception()\nException"
    )

    # When
    logger.info("hello %s, %d", "arg1", 22.22)
    _log_traceback()

    # Then
    assert [json.loads(message) for message in caplog.text.split("\n") if message] == [
        {
            "levelname": "INFO",
            "message": "hello arg1, 22",
            "timestamp": "2023-12-08 06:05:47,000",
            "logger_name": "test_json_formatter__outputs_expected",
            "pid": expected_pid,
            "thread_name": "MainThread",
        },
        {
            "levelname": "ERROR",
            "message": "this is an error",
            "timestamp": "2023-12-08 06:05:47,000",
            "logger_name": "test_json_formatter__outputs_expected",
            "pid": expected_pid,
            "thread_name": "MainThread",
            "exc_info": expected_tb_string,
        },
    ]


def test_setup_logging__generic_format__configures_stdlib(
    capsys: pytest.CaptureFixture[str],
    test_app_loggers: list[str],
) -> None:
    # Given
    setup_logging(
        log_level="DEBUG", log_format="generic", application_loggers=test_app_loggers
    )
    test_logger = logging.getLogger("test.generic")

    # When
    test_logger.info("hello world")

    # Then
    output = capsys.readouterr().out
    assert "hello world" in output


def test_setup_logging__json_format__stdlib_outputs_json(
    capsys: pytest.CaptureFixture[str],
    test_app_loggers: list[str],
) -> None:
    # Given
    setup_logging(
        log_level="DEBUG", log_format="json", application_loggers=test_app_loggers
    )
    test_logger = logging.getLogger("test.json_stdlib")

    # When
    test_logger.info("stdlib json message")

    # Then
    output = capsys.readouterr().out.strip()
    parsed = json.loads(output)
    assert parsed["message"] == "stdlib json message"
    assert parsed["levelname"] == "INFO"
    assert parsed["logger_name"] == "test.json_stdlib"
    assert "pid" in parsed
    assert "thread_name" in parsed


def test_setup_logging__json_format__structlog_outputs_json(
    capsys: pytest.CaptureFixture[str],
    test_app_loggers: list[str],
) -> None:
    # Given
    setup_logging(
        log_level="DEBUG", log_format="json", application_loggers=test_app_loggers
    )
    structured_logger = structlog.get_logger("test.json_structlog")

    # When
    structured_logger.info("structlog json message", extra_key="extra_value")

    # Then
    output = capsys.readouterr().out.strip()
    parsed = json.loads(output)
    assert parsed["message"] == "structlog json message"
    assert parsed["levelname"] == "INFO"
    assert parsed["logger_name"] == "test.json_structlog"
    assert parsed["pid"] == os.getpid()
    assert parsed["extra_key"] == "extra_value"


def test_setup_logging__generic_format__structlog_outputs_console(
    capsys: pytest.CaptureFixture[str],
    test_app_loggers: list[str],
) -> None:
    # Given
    setup_logging(
        log_level="DEBUG", log_format="generic", application_loggers=test_app_loggers
    )
    structured_logger = structlog.get_logger("test.generic_structlog")

    # When
    structured_logger.info("structlog console message")

    # Then
    output = capsys.readouterr().out
    assert "structlog console message" in output


def test_setup_logging__custom_config_file__loads_dictconfig(
    tmp_path: Path,
) -> None:
    # Given
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "custom_config_test": {
                "level": "CRITICAL",
                "handlers": ["console"],
            },
        },
    }
    config_file = tmp_path / "logging.json"
    config_file.write_text(json.dumps(config))

    # When
    setup_logging(logging_configuration_file=str(config_file))

    # Then
    custom_logger = logging.getLogger("custom_config_test")
    assert custom_logger.level == logging.CRITICAL


def test_setup_logging__structlog_configured__sentry_processor_wired(
    capsys: pytest.CaptureFixture[str],
    test_app_loggers: list[str],
) -> None:
    # Given
    setup_logging(
        log_level="DEBUG",
        log_format="generic",
        application_loggers=test_app_loggers,
    )
    structured_logger = structlog.get_logger("test.sentry_proc")

    # When
    with patch("common.core.sentry.sentry_sdk") as mock_sentry:
        structured_logger.info("test sentry context", environment_id="env-1")

    # Then
    mock_sentry.set_context.assert_called_once()
    context = mock_sentry.set_context.call_args[0][1]
    assert context["environment_id"] == "env-1"


def test_setup_logging__json_format__structlog_exception_included(
    capsys: pytest.CaptureFixture[str],
    test_app_loggers: list[str],
) -> None:
    # Given
    setup_logging(
        log_level="DEBUG", log_format="json", application_loggers=test_app_loggers
    )
    structured_logger = structlog.get_logger("test.exc")

    # When
    try:
        raise ValueError("boom")
    except ValueError:
        structured_logger.exception("something failed")

    # Then
    output = capsys.readouterr().out.strip()
    parsed = json.loads(output)
    assert parsed["message"] == "something failed"
    assert parsed["levelname"] == "ERROR"
    assert "exc_info" in parsed
    assert "ValueError: boom" in parsed["exc_info"]


def test_setup_logging__json_format__stdlib_and_structlog_same_schema(
    capsys: pytest.CaptureFixture[str],
    test_app_loggers: list[str],
) -> None:
    # Given
    setup_logging(
        log_level="DEBUG", log_format="json", application_loggers=test_app_loggers
    )
    stdlib_logger = logging.getLogger("test.schema.stdlib")
    structured_logger = structlog.get_logger("test.schema.structlog")

    # When
    stdlib_logger.info("stdlib message")
    stdlib_output = capsys.readouterr().out.strip()

    structured_logger.info("structlog message")
    structlog_output = capsys.readouterr().out.strip()

    # Then
    expected_keys = {
        "timestamp",
        "message",
        "levelname",
        "logger_name",
        "pid",
        "thread_name",
    }
    stdlib_keys = set(json.loads(stdlib_output).keys())
    structlog_keys = set(json.loads(structlog_output).keys())
    assert stdlib_keys == structlog_keys == expected_keys


def test_setup_logging__info_level__root_at_warning() -> None:
    # Given / When
    setup_logging(log_level="INFO", log_format="generic")

    # Then
    root = logging.getLogger()
    assert root.level == logging.WARNING


def test_setup_logging__debug_level__root_at_debug() -> None:
    # Given / When
    setup_logging(log_level="DEBUG", log_format="generic")

    # Then
    root = logging.getLogger()
    assert root.level == logging.DEBUG


def test_setup_logging__application_loggers__set_to_log_level() -> None:
    # Given / When
    setup_logging(
        log_level="INFO",
        log_format="generic",
        application_loggers=["myapp", "mylib"],
    )

    # Then
    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert logging.getLogger("myapp").level == logging.INFO
    assert logging.getLogger("mylib").level == logging.INFO


def test_setup_logging__application_loggers__third_party_filtered(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given
    setup_logging(log_level="INFO", log_format="generic", application_loggers=["myapp"])
    app_logger = logging.getLogger("myapp.views")
    third_party_logger = logging.getLogger("urllib3.connectionpool")

    # When
    app_logger.info("app message")
    third_party_logger.info("noisy third-party message")

    # Then
    output = capsys.readouterr().out
    assert "app message" in output
    assert "noisy third-party message" not in output


def test_setup_logging__stdlib_error__sentry_captures_clean_message(
    capsys: pytest.CaptureFixture[str],
    test_app_loggers: list[str],
    sentry_transport_mock: "MockSentryTransport",
) -> None:
    """Verify Sentry receives the original message, not the rendered output.

    Sentry's ``LoggingIntegration`` monkey-patches ``Logger.callHandlers``
    and reads ``record.msg`` / ``record.args`` in a ``finally`` block
    *after* all handlers (and formatters) have run::

        try:
            old_callhandlers(self, record)  # formatters run here
        finally:
            integration._handle_record(record)  # reads record.msg

    structlog's ``ProcessorFormatter.format()`` replaces ``record.msg``
    with rendered output (JSON/console) and clears ``record.args`` to
    ``()``.  Without ``_SentryFriendlyProcessorFormatter``, Sentry would
    see a JSON blob as the message — breaking event grouping because every
    rendered string (containing timestamps, PIDs, …) is unique.

    ``_SentryFriendlyProcessorFormatter`` snapshots and restores the
    originals so Sentry sees the clean message template and args.
    """
    # Given
    setup_logging(
        log_level="DEBUG", log_format="json", application_loggers=test_app_loggers
    )
    test_logger = logging.getLogger("test.sentry_compat")

    # When
    test_logger.error("order %s failed for %s", "ORD-123", "alice")

    # Then — the stream got JSON
    output = capsys.readouterr().out.strip()
    parsed = json.loads(output)
    assert parsed["message"] == "order ORD-123 failed for alice"

    # And — Sentry received the original message template, not the JSON blob.
    assert len(sentry_transport_mock.events) == 1
    logentry = sentry_transport_mock.events[0]["logentry"]
    assert logentry["message"] == "order %s failed for %s"
    assert logentry["params"] == ["ORD-123", "alice"]
    assert logentry["formatted"] == "order ORD-123 failed for alice"


def test_setup_logging__structlog_error__sentry_captures_with_context(
    capsys: pytest.CaptureFixture[str],
    test_app_loggers: list[str],
    sentry_transport_mock: "MockSentryTransport",
) -> None:
    """Verify structlog errors reach Sentry with context from sentry_processor."""
    # Given
    setup_logging(
        log_level="DEBUG", log_format="json", application_loggers=test_app_loggers
    )
    structured_logger = structlog.get_logger("test.sentry_structlog")

    # When
    structured_logger.error("payment failed", order_id="ORD-456")

    # Then — Sentry captured the event
    assert len(sentry_transport_mock.events) == 1
    event = sentry_transport_mock.events[0]

    # And — sentry_processor set the structlog context
    assert "structlog" in event["contexts"]
    assert event["contexts"]["structlog"]["order_id"] == "ORD-456"


def test_setup_logging__default_args__root_at_warning() -> None:
    # Given / When
    setup_logging()

    # Then
    root = logging.getLogger()
    assert root.level == logging.WARNING
