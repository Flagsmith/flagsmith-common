import json
import logging
import logging.config
import os
import sys
import threading
from typing import Any

import structlog
import structlog.contextvars
import structlog.dev
import structlog.processors
import structlog.stdlib
from structlog.typing import EventDict, Processor, WrappedLogger
from typing_extensions import TypedDict

from common.core.constants import LOGGING_DEFAULT_ROOT_LOG_LEVEL

logger = logging.getLogger(__name__)


class JsonRecord(TypedDict, extra_items=Any, total=False):  # type: ignore[call-arg]  # TODO https://github.com/python/mypy/issues/18176
    levelname: str
    message: str
    timestamp: str
    logger_name: str
    pid: int | None
    thread_name: str | None
    exc_info: str


class JsonFormatter(logging.Formatter):
    """Custom formatter for json logs."""

    def get_json_record(self, record: logging.LogRecord) -> JsonRecord:
        formatted_message = record.getMessage()
        json_record: JsonRecord = {
            "levelname": record.levelname,
            "message": formatted_message,
            "timestamp": self.formatTime(record, self.datefmt),
            "logger_name": record.name,
            "pid": record.process,
            "thread_name": record.threadName,
        }
        if record.exc_info:
            json_record["exc_info"] = self.formatException(record.exc_info)
        return json_record

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(self.get_json_record(record))


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "generic",
    logging_configuration_file: str | None = None,
    application_loggers: list[str] | None = None,
    extra_foreign_processors: list[Processor] | None = None,
) -> None:
    """
    Set up logging for the application.

    This should be called early, before Django settings are loaded, to ensure
    that all log output is properly formatted from the start.

    Args:
        log_level: The log level for application code (e.g. "DEBUG", "INFO").
        log_format: Either "generic" or "json".
        logging_configuration_file: Path to a JSON logging config file.
            If provided, this takes precedence over other format options.
        application_loggers: Top-level logger names for application packages.
            These loggers are set to ``log_level`` while the root logger uses
            ``max(log_level, WARNING)`` to suppress noise from third-party
            libraries. If ``log_level`` is DEBUG, everything logs at DEBUG.
        extra_foreign_processors: Additional structlog processors to run in
            the ``foreign_pre_chain`` for stdlib log records (e.g. the
            Gunicorn access log field extractor).
    """
    if logging_configuration_file:
        with open(logging_configuration_file) as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        log_level_int = logging.getLevelNamesMapping()[log_level.upper()]
        root_level_int = logging.getLevelNamesMapping()[LOGGING_DEFAULT_ROOT_LOG_LEVEL]
        # Suppress third-party noise at WARNING, but if the user requests
        # DEBUG, honour that for the entire process.
        effective_root_level = (
            log_level_int if log_level_int < logging.INFO else root_level_int
        )

        dict_config: dict[str, Any] = {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "level": log_level,
                },
            },
            "root": {
                "level": effective_root_level,
                "handlers": ["console"],
            },
            "loggers": {
                name: {"level": log_level, "handlers": [], "propagate": True}
                for name in application_loggers or []
            },
        }
        logging.config.dictConfig(dict_config)

    setup_structlog(
        log_format=log_format, extra_foreign_processors=extra_foreign_processors
    )


def map_event_to_json_record(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Map structlog fields to match :class:`JsonFormatter` output schema."""
    record: JsonRecord = {
        "message": event_dict.pop("event", ""),
        "levelname": event_dict.pop("level", "").upper(),
        "logger_name": event_dict.pop("logger", ""),
        "pid": os.getpid(),
        "thread_name": threading.current_thread().name,
    }
    if "exception" in event_dict:
        record["exc_info"] = event_dict.pop("exception")
    # Merge remaining structlog keys (e.g. extra_key from bind()) with the
    # canonical record so they appear in the JSON output.
    event_dict.update(record)
    return event_dict


class _SentryFriendlyProcessorFormatter(structlog.stdlib.ProcessorFormatter):
    """Preserves ``record.msg`` and ``record.args`` across formatting.

    Sentry's ``LoggingIntegration`` reads these fields *after* handlers run;
    structlog's ``ProcessorFormatter`` replaces them with rendered output, breaking event
    grouping. We snapshot before and restore after so Sentry sees the originals
    and avoids failed event deduplication.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Snapshot the original fields before ProcessorFormatter
        # replaces them with rendered output.
        original_msg = record.msg
        original_args = record.args

        # Stash original args on the record so foreign_pre_chain
        # processors (e.g. the Gunicorn access log extractor) can
        # access them — ProcessorFormatter clears record.args to ()
        # before running the chain.
        record._original_args = original_args

        formatted = super().format(record)

        # Restore so Sentry (and any other post-handler hook) sees
        # the original message template and substitution args.
        record.msg = original_msg
        record.args = original_args
        del record._original_args  # type: ignore[attr-defined]

        return formatted

    @staticmethod
    def drop_internal_keys(
        _: WrappedLogger, __: str, event_dict: EventDict
    ) -> EventDict:
        """Remove internal attributes that leak via ``ExtraAdder``."""
        event_dict.pop("_original_args", None)
        return event_dict


def build_processor_formatter(
    log_format: str,
    extra_foreign_processors: list[Processor] | None = None,
) -> _SentryFriendlyProcessorFormatter:
    """Build a ``_SentryFriendlyProcessorFormatter`` for the given log format.

    This is used by :func:`setup_structlog` for the root logger.
    """
    if log_format == "json":
        renderer_processors: list[Processor] = [
            map_event_to_json_record,
            structlog.processors.JSONRenderer(),
        ]
    else:
        colors = sys.stdout.isatty() and structlog.dev._has_colors
        renderer_processors = [
            structlog.dev.ConsoleRenderer(colors=colors),
        ]

    foreign_pre_chain: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
        _SentryFriendlyProcessorFormatter.drop_internal_keys,
        *(extra_foreign_processors or []),
    ]

    return _SentryFriendlyProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *renderer_processors,
        ],
        foreign_pre_chain=foreign_pre_chain,
    )


def setup_structlog(
    log_format: str,
    extra_foreign_processors: list[Processor] | None = None,
) -> None:
    """Configure structlog to route through stdlib logging."""
    from common.core.sentry import sentry_processor

    formatter = build_processor_formatter(
        log_format, extra_foreign_processors=extra_foreign_processors
    )

    # Replace the formatter on existing root handlers with ProcessorFormatter.
    root = logging.getLogger()
    for handler in root.handlers:
        handler.setFormatter(formatter)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            sentry_processor,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
