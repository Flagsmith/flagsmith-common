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
from common.core.sentry import sentry_processor

logger = logging.getLogger(__name__)


class JsonRecord(TypedDict, extra_items=Any, total=False):  # type: ignore[call-arg]  # TODO https://github.com/python/mypy/issues/18176
    levelname: str
    message: str
    timestamp: str
    logger_name: str
    pid: int | None
    thread_name: str | None
    exc_info: str


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
    """Map structlog fields to match :class:`JsonRecord` output schema."""
    # Remove foreign record args injected by pass_foreign_args so they
    # don't leak into the rendered JSON output.
    event_dict.pop("positional_args", None)
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


def setup_structlog(
    log_format: str,
    extra_foreign_processors: list[Processor] | None = None,
) -> None:
    """Configure structlog to route through stdlib logging.

    Sentry compatibility is handled by structlog itself: since 24.1,
    ``ProcessorFormatter.format()`` operates on a shallow copy of the
    record, leaving the original ``msg``, ``args``, and ``exc_info``
    intact for Sentry's ``LoggingIntegration`` hook.
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
        structlog.processors.format_exc_info,
        structlog.stdlib.ExtraAdder(),
        *(extra_foreign_processors or []),
    ]

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *renderer_processors,
        ],
        foreign_pre_chain=foreign_pre_chain,
        pass_foreign_args=True,
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
