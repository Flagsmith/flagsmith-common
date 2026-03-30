import json
from datetime import datetime, timezone

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
from opentelemetry.util.types import AnyValue
from structlog.typing import EventDict, Processor

_SEVERITY_MAP: dict[str, SeverityNumber] = {
    "debug": SeverityNumber.DEBUG,
    "info": SeverityNumber.INFO,
    "warning": SeverityNumber.WARN,
    "error": SeverityNumber.ERROR,
    "critical": SeverityNumber.FATAL,
}

_RESERVED_KEYS = frozenset({"event", "level", "timestamp", "logger"})


def make_structlog_otel_processor(logger_provider: LoggerProvider) -> Processor:
    """Create a structlog processor that emits log records to OpenTelemetry.

    Sits in the processor chain *before* the final renderer so that
    only structlog-originated logs reach OTel.  Passes the event_dict
    through unchanged so downstream processors (console/JSON renderers)
    still work normally.

    Pass the returned processor to :func:`~common.core.logging.setup_logging`
    via ``otel_processor``.
    """

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

        otel_logger = logger_provider.get_logger(logger_name or __name__)
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


def setup_tracing(tracer_provider: TracerProvider) -> None:
    """Set up OTel distributed tracing with Django instrumentation.

    Sets the global TracerProvider, configures W3C trace context +
    baggage propagation, and instruments Django so that every request
    creates a span with the incoming trace context.

    Must be called *before* Django's WSGI app is created.
    """
    trace.set_tracer_provider(tracer_provider)

    propagator: TextMapPropagator = CompositePropagator(
        [
            TraceContextTextMapPropagator(),
            W3CBaggagePropagator(),
        ]
    )
    set_global_textmap(propagator)

    DjangoInstrumentor().instrument()
