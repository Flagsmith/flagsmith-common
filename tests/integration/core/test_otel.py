from typing import Generator

import pytest
import pytest_mock
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
from opentelemetry.trace import SpanKind
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
    setup_logging(
        application_loggers=["mylogger"],
        otel_processors=otel_processors,
    )
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
    structlog.get_logger("mylogger").info(
        "scan-created",
        code_references__count=3,
        feature__count=2,
    )

    # Then
    records = log_exporter.get_finished_logs()
    assert len(records) == 1

    log_record = records[0].log_record
    assert log_record.body == "scan-created"
    assert log_record.event_name == "mylogger.scan_created"
    assert log_record.severity_number == SeverityNumber.INFO

    attrs = log_record.attributes
    assert attrs is not None
    assert attrs["code_references.count"] == 3
    assert attrs["feature.count"] == 2
    assert attrs["flagsmith.event"] == "mylogger.scan_created"


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
        structlog.get_logger("mylogger").info("event-tracked")
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
    structlog.get_logger("mylogger").info("scan-created")

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
def test_django_tracing__get_request__creates_http_and_db_spans(
    client: APIClient,
    span_exporter: InMemorySpanExporter,
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Given
    ANY = mocker.ANY

    # When
    response = client.get("/version/")

    # Then
    assert response.status_code == 200

    spans = sorted(span_exporter.get_finished_spans(), key=lambda s: s.name)
    assert [(s.name, s.kind) for s in spans] == [
        ("GET /version/", SpanKind.SERVER),
        ("SELECT", SpanKind.CLIENT),
        ("SELECT", SpanKind.CLIENT),
    ]

    http_span, db_span_1, db_span_2 = spans

    assert dict(http_span.attributes or {}) == {
        "http.method": "GET",
        "http.url": "http://testserver/version/",
        "http.route": "version/",
        "http.scheme": "http",
        "http.server_name": "testserver",
        "http.flavor": "1.1",
        "http.status_code": 200,
        "net.host.port": 80,
        "net.peer.ip": "127.0.0.1",
    }
    assert http_span.parent is None
    assert http_span.resource.attributes["service.name"] == "test-service"

    assert dict(db_span_1.attributes or {}) == {
        "db.system": "postgresql",
        "db.name": ANY,
        "db.user": ANY,
        "db.statement": 'SELECT %s AS "a" FROM "auth_user" LIMIT 1',
        "net.peer.name": "localhost",
        "net.peer.port": 6543,
    }
    assert db_span_1.parent is not None
    assert db_span_1.parent.span_id == http_span.context.span_id

    assert dict(db_span_2.attributes or {}) == {
        "db.system": "postgresql",
        "db.name": ANY,
        "db.user": ANY,
        "db.statement": (
            'SELECT %s AS "a" FROM "auth_user"'
            ' WHERE "auth_user"."last_login" IS NOT NULL LIMIT 1'
        ),
        "net.peer.name": "localhost",
        "net.peer.port": 6543,
    }
    assert db_span_2.parent is not None
    assert db_span_2.parent.span_id == http_span.context.span_id


@pytest.mark.django_db
def test_django_tracing__request_with_traceparent__propagates_to_all_spans(
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
    spans = sorted(span_exporter.get_finished_spans(), key=lambda s: s.name)
    assert len(spans) == 3

    http_span = spans[0]
    assert http_span.name == "GET /version/"
    assert f"{http_span.context.trace_id:032x}" == trace_id
    assert http_span.parent is not None
    assert f"{http_span.parent.span_id:016x}" == parent_span_id

    for db_span in spans[1:]:
        assert db_span.name == "SELECT"
        assert f"{db_span.context.trace_id:032x}" == trace_id
        assert db_span.parent is not None
        assert db_span.parent.span_id == http_span.context.span_id


@pytest.mark.django_db
def test_django_tracing__request_with_baggage__propagates_trace_context(
    client: APIClient,
    span_exporter: InMemorySpanExporter,
) -> None:
    # Given
    trace_id = "0af7651916cd43dd8448eb211c80319c"
    traceparent = f"00-{trace_id}-b7ad6b7169203331-01"
    baggage_header = "amplitude.device_id=dev-42,amplitude.session_id=sess-99"

    # When
    client.get(
        "/version/",
        HTTP_TRACEPARENT=traceparent,
        HTTP_BAGGAGE=baggage_header,
    )

    # Then — all spans share the propagated trace ID
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 3
    for span in spans:
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
