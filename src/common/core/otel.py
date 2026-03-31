import contextlib
import json
from collections.abc import Generator
from datetime import datetime, timezone
from importlib.metadata import version
from typing import cast

import inflection
import structlog
from opentelemetry import baggage, trace
from opentelemetry import context as otel_context
from opentelemetry._logs import SeverityNumber
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.exporter.otlp.proto.http._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.textmap import TextMapPropagator
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)
from opentelemetry.util.types import AnyValue, Attributes
from structlog.typing import EventDict, Processor

_SEVERITY_MAP: dict[str, SeverityNumber] = {
    "debug": SeverityNumber.DEBUG,
    "info": SeverityNumber.INFO,
    "warning": SeverityNumber.WARN,
    "error": SeverityNumber.ERROR,
    "critical": SeverityNumber.FATAL,
}

_RESERVED_KEYS = frozenset(
    [
        "event",
        "level",
        "timestamp",
        "logger",
        "trace_id",
        "span_id",
    ]
)


def add_otel_trace_context(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Add ``trace_id`` and ``span_id`` from the active OTel span to the event dict."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.is_valid:
        event_dict["trace_id"] = f"{ctx.trace_id:032x}"
        event_dict["span_id"] = f"{ctx.span_id:016x}"
    return event_dict


def make_structlog_otel_processor(logger_provider: LoggerProvider) -> Processor:
    """Create a structlog processor that emits log records to OpenTelemetry.

    Sits in the processor chain *before* the final renderer so that
    only structlog-originated logs reach OTel.  Passes the event_dict
    through unchanged so downstream processors (console/JSON renderers)
    still work normally.

    Pass the returned processor to :func:`~common.core.logging.setup_logging`
    via ``otel_processor``.
    """
    otel_logger = logger_provider.get_logger(__name__, version("flagsmith-common"))

    def processor(
        logger: structlog.types.WrappedLogger,
        method_name: str,
        event_dict: EventDict,
    ) -> EventDict:
        attributes = map_event_dict_to_otel_attributes(event_dict)

        # Copy W3C baggage entries into log attributes so downstream
        # exporters can access them.
        ctx = otel_context.get_current()
        for key, value in baggage.get_all(ctx).items():
            attributes[key] = str(value)

        body = event_dict.get("event", "")
        logger_name = event_dict.get("logger")
        event_name = inflection.underscore(body)
        if logger_name:
            event_name = f"{logger_name}.{event_name}"

        otel_logger.emit(
            timestamp=int(datetime.now(timezone.utc).timestamp() * 1e9),
            context=otel_context.get_current(),
            severity_number=map_event_dict_to_otel_severity_number(
                event_dict=event_dict,
                method_name=method_name,
            ),
            body=body,
            event_name=event_name,
            attributes=attributes,
        )

        # Also attach as a span event if there's an active span.
        span = trace.get_current_span()
        if span.is_recording():
            # AnyValue is a superset of AttributeValue at runtime;
            # the cast keeps mypy happy.
            span.add_event(event_name, attributes=cast(Attributes, attributes))

        return event_dict

    return processor


def map_event_dict_to_otel_severity_number(
    event_dict: EventDict,
    method_name: str,
) -> SeverityNumber:
    level = event_dict.get("level", method_name)
    return _SEVERITY_MAP.get(level, SeverityNumber.INFO)


def map_event_dict_to_otel_attributes(event_dict: EventDict) -> dict[str, AnyValue]:
    return {
        k.replace("__", "."): map_value_to_otel_value(v)
        for k, v in event_dict.items()
        if k not in _RESERVED_KEYS
    }


def map_value_to_otel_value(value: object) -> str | int | float | bool:
    """Coerce a value to an OTel-attribute-compatible type."""
    if isinstance(value, (bool, str, int, float)):
        return value
    return json.dumps(value, default=str)


def build_otel_log_provider(*, endpoint: str, service_name: str) -> LoggerProvider:
    """Create and configure an OTel LoggerProvider with OTLP/HTTP export."""
    resource = Resource.create({"service.name": service_name})
    provider = LoggerProvider(resource=resource)
    exporter = OTLPLogExporter(endpoint=endpoint)
    provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    return provider


def build_tracer_provider(*, endpoint: str, service_name: str) -> TracerProvider:
    """Create a TracerProvider with OTLP/HTTP export."""
    resource = Resource.create({"service.name": service_name})
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=endpoint)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    return tracer_provider


@contextlib.contextmanager
def setup_tracing(
    tracer_provider: TracerProvider,
    excluded_urls: str | None = None,
) -> Generator[None, None, None]:
    """Set up and tear down OTel distributed tracing with Django instrumentation.

    Sets the global TracerProvider, configures W3C trace context +
    baggage propagation, and instruments Django so that every request
    creates a span with the incoming trace context.

    On exit, uninstruments Django and shuts down the tracer provider.

    Must be called *before* Django's WSGI app is created.

    Args:
        tracer_provider: The TracerProvider to use.
        excluded_urls: Comma-separated URL paths to exclude from tracing
            (e.g. ``"health/liveness,health/readiness"``). If not provided,
            falls back to the ``OTEL_PYTHON_DJANGO_EXCLUDED_URLS`` env var.
    """
    trace.set_tracer_provider(tracer_provider)

    propagator: TextMapPropagator = CompositePropagator(
        [
            TraceContextTextMapPropagator(),
            W3CBaggagePropagator(),
        ]
    )
    set_global_textmap(propagator)

    DjangoInstrumentor().instrument(excluded_urls=excluded_urls)
    Psycopg2Instrumentor().instrument(enable_commenter=True, skip_dep_check=True)
    RedisInstrumentor().instrument()
    try:
        yield
    finally:
        RedisInstrumentor().uninstrument()
        Psycopg2Instrumentor().uninstrument()
        DjangoInstrumentor().uninstrument()
        tracer_provider.shutdown()
