import sentry_sdk
from structlog.typing import EventDict, WrappedLogger

_SKIP_CONTEXT_FIELDS = frozenset({"event", "level", "timestamp", "_record"})


def sentry_processor(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """
    Structlog processor that enriches Sentry with structured context and tags.

    Since structlog routes through stdlib, Sentry's LoggingIntegration
    automatically captures ERROR+ logs as Sentry events. This processor
    adds structured context on top of that.
    """
    context = {k: v for k, v in event_dict.items() if k not in _SKIP_CONTEXT_FIELDS}
    sentry_sdk.set_context("structlog", context)

    return event_dict
