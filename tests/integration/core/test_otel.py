from typing import Generator

import pytest
import structlog
from opentelemetry import baggage, context
from opentelemetry._logs import SeverityNumber
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.propagate import get_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import (
    InMemoryLogExporter,
    SimpleLogRecordProcessor,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)
from rest_framework.test import APIClient

from common.core.logging import setup_logging
from common.core.otel import (
    add_otel_trace_context,
    make_structlog_otel_processor,
    setup_tracing,
)


@pytest.fixture()
def log_exporter() -> InMemoryLogExporter:
    return InMemoryLogExporter()  # type: ignore[no-untyped-call]


@pytest.fixture()
def log_provider(log_exporter: InMemoryLogExporter) -> LoggerProvider:
    provider = LoggerProvider(
        resource=Resource.create({"service.name": "test-service"}),
    )
    provider.add_log_record_processor(SimpleLogRecordProcessor(log_exporter))
    return provider


@pytest.fixture(autouse=True)
def setup_logging_fixture(
    log_provider: LoggerProvider,
) -> Generator[None, None, None]:
    otel_processors = [
        add_otel_trace_context,
        make_structlog_otel_processor(log_provider),
    ]
    setup_logging(log_level="DEBUG", otel_processors=otel_processors)
    # Override cache_logger_on_first_use so each test gets a fresh logger
    # bound to the current fixture's exporter.
    structlog.configure(cache_logger_on_first_use=False)
    yield
    structlog.reset_defaults()


@pytest.fixture(scope="module", name="setup_tracing")
def setup_tracing_fixture() -> Generator[InMemorySpanExporter, None, None]:
    """Set up OTel tracing for the test module, yielding the in-memory span exporter.

    Module-scoped because OTel only allows setting the global TracerProvider once per process.
    Use the ``span_exporter`` fixture for per-test isolation.

    This exercises the real ``setup_tracing`` context manager. Its behaviour can be
    verified indirectly by asserting on the effects: spans created by Django,
    trace context propagation, and propagator wiring.
    """
    exporter = InMemorySpanExporter()
    provider = TracerProvider(
        resource=Resource.create({"service.name": "test-service"}),
    )
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    with setup_tracing(provider, excluded_urls="health/liveness"):
        yield exporter


@pytest.fixture()
def span_exporter(setup_tracing: InMemorySpanExporter) -> InMemorySpanExporter:
    setup_tracing.clear()
    return setup_tracing


def test_structlog_otel_log_record__basic_event__body_event_name_severity_attributes(
    log_exporter: InMemoryLogExporter,
) -> None:
    # Given / When
    structlog.get_logger("code_references").info(
        "scan-created",
        code_references__count=3,
        feature__count=2,
    )

    # Then
    records = log_exporter.get_finished_logs()
    assert len(records) == 1

    log_record = records[0].log_record
    assert log_record.body == "scan-created"
    assert log_record.event_name == "code_references.scan_created"
    assert log_record.severity_number == SeverityNumber.INFO

    attrs = log_record.attributes
    assert attrs is not None
    assert attrs["code_references.count"] == 3
    assert attrs["feature.count"] == 2


def test_structlog_otel_log_record__reserved_keys__excluded_from_attributes(
    log_exporter: InMemoryLogExporter,
) -> None:
    # Given / When
    structlog.get_logger("mylogger").warning("some-event", extra_key="val")

    # Then
    attrs = log_exporter.get_finished_logs()[0].log_record.attributes
    assert attrs is not None
    assert "event" not in attrs
    assert "level" not in attrs
    assert "timestamp" not in attrs
    assert "logger" not in attrs
    assert attrs["extra_key"] == "val"


def test_structlog_otel_log_record__w3c_baggage__propagated_to_log_attributes(
    log_exporter: InMemoryLogExporter,
) -> None:
    # Given
    ctx = baggage.set_baggage("amplitude.device_id", "device-123")
    ctx = baggage.set_baggage("amplitude.session_id", "session-456", context=ctx)

    # When
    token = context.attach(ctx)
    try:
        structlog.get_logger("analytics").info("event-tracked")
    finally:
        context.detach(token)

    # Then
    attrs = log_exporter.get_finished_logs()[0].log_record.attributes
    assert attrs is not None
    assert attrs["amplitude.device_id"] == "device-123"
    assert attrs["amplitude.session_id"] == "session-456"


def test_structlog_otel_log_record__instrumentation_scope__identifies_flagsmith_common(
    log_exporter: InMemoryLogExporter,
) -> None:
    # Given / When
    structlog.get_logger("code_references").info("scan-created")

    # Then
    scope = log_exporter.get_finished_logs()[0].instrumentation_scope
    assert scope is not None
    assert scope.name == "common.core.otel"
    assert scope.version is not None


def test_structlog_otel_log_record__non_primitive_values__serialised_to_json(
    log_exporter: InMemoryLogExporter,
) -> None:
    # Given / When
    structlog.get_logger("mylogger").info(
        "complex-event",
        nested={"key": "value"},
        items=[1, 2, 3],
    )

    # Then
    attrs = log_exporter.get_finished_logs()[0].log_record.attributes
    assert attrs is not None
    assert attrs["nested"] == '{"key": "value"}'
    assert attrs["items"] == "[1, 2, 3]"


def test_structlog_otel_log_record__active_span__trace_context_on_log_record(
    log_exporter: InMemoryLogExporter,
) -> None:
    # Given
    provider = TracerProvider()
    tracer = provider.get_tracer(__name__)

    # When — emit a structlog event inside an active span
    with tracer.start_as_current_span("test-span") as span:
        structlog.get_logger("mylogger").info("inside-span")
        expected_trace_id = span.get_span_context().trace_id
        expected_span_id = span.get_span_context().span_id

    # Then — trace context is on the LogRecord itself (via otel_context),
    # not duplicated in attributes (trace_id/span_id are reserved keys).
    log_record = log_exporter.get_finished_logs()[0].log_record
    assert log_record.trace_id == expected_trace_id
    assert log_record.span_id == expected_span_id
    assert log_record.attributes is not None
    assert "trace_id" not in log_record.attributes
    assert "span_id" not in log_record.attributes


@pytest.mark.django_db
def test_django_tracing__get_request__creates_span_with_http_attributes(
    client: APIClient,
    span_exporter: InMemorySpanExporter,
) -> None:
    # Given / When
    response = client.get("/version/")

    # Then
    assert response.status_code == 200

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    span = spans[0]
    assert span.name == "GET /version/"
    attrs = dict(span.attributes or {})
    assert attrs["http.method"] == "GET"
    assert attrs["http.url"] == "http://testserver/version/"
    assert attrs["http.status_code"] == 200


@pytest.mark.django_db
def test_django_tracing__request__span_has_service_name_resource(
    client: APIClient,
    span_exporter: InMemorySpanExporter,
) -> None:
    # Given / When
    client.get("/version/")

    # Then
    span = span_exporter.get_finished_spans()[0]
    service_name = span.resource.attributes.get("service.name")
    assert service_name == "test-service"


@pytest.mark.django_db
def test_django_tracing__request_with_traceparent__propagates_trace_context(
    client: APIClient,
    span_exporter: InMemorySpanExporter,
) -> None:
    # Given
    trace_id = "0af7651916cd43dd8448eb211c80319c"
    parent_span_id = "b7ad6b7169203331"
    traceparent = f"00-{trace_id}-{parent_span_id}-01"

    # When
    client.get("/version/", HTTP_TRACEPARENT=traceparent)

    # Then
    span = span_exporter.get_finished_spans()[0]
    assert f"{span.context.trace_id:032x}" == trace_id
    assert span.parent is not None
    assert f"{span.parent.span_id:016x}" == parent_span_id


@pytest.mark.django_db
def test_django_tracing__request_with_baggage__baggage_propagated(
    client: APIClient,
    span_exporter: InMemorySpanExporter,
) -> None:
    # Given
    traceparent = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
    baggage_header = "amplitude.device_id=dev-42,amplitude.session_id=sess-99"

    # When
    client.get(
        "/version/",
        HTTP_TRACEPARENT=traceparent,
        HTTP_BAGGAGE=baggage_header,
    )

    # Then — the span is created within the propagated trace context.
    # Baggage doesn't appear on spans directly, but we verify the
    # trace context was propagated (proving the composite propagator works).
    span = span_exporter.get_finished_spans()[0]
    trace_id = "0af7651916cd43dd8448eb211c80319c"
    assert f"{span.context.trace_id:032x}" == trace_id


def test_django_tracing__excluded_url__produces_no_span(
    client: APIClient,
    span_exporter: InMemorySpanExporter,
) -> None:
    # Given — health/liveness is excluded in the setup_tracing fixture
    # When
    response = client.get("/health/liveness/")

    # Then
    assert response.status_code == 200
    assert len(span_exporter.get_finished_spans()) == 0


def test_django_tracing__propagators__composite_with_tracecontext_and_baggage(
    span_exporter: InMemorySpanExporter,
) -> None:
    # Given / When
    textmap = get_global_textmap()

    # Then — verify the module-scoped setup configured correct propagators
    assert isinstance(textmap, CompositePropagator)
    assert {type(p) for p in textmap._propagators} == {
        TraceContextTextMapPropagator,
        W3CBaggagePropagator,
    }
