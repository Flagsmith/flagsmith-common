from typing import Generator

import pytest
import structlog
from opentelemetry import baggage, context
from opentelemetry._logs import SeverityNumber
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import (
    InMemoryLogExporter,
    SimpleLogRecordProcessor,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from common.core.otel import (
    build_otel_log_provider,
    build_tracer_provider,
    make_structlog_otel_processor,
)


@pytest.fixture()
def otel_exporter() -> InMemoryLogExporter:
    return InMemoryLogExporter()  # type: ignore[no-untyped-call]


@pytest.fixture()
def otel_processor(otel_exporter: InMemoryLogExporter) -> structlog.typing.Processor:
    provider = LoggerProvider(
        resource=Resource.create({"service.name": "test"}),
    )
    provider.add_log_record_processor(SimpleLogRecordProcessor(otel_exporter))
    return make_structlog_otel_processor(provider)


@pytest.fixture(autouse=True)
def add_otel_processor(
    otel_processor: structlog.typing.Processor,
) -> Generator[None, None, None]:
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            otel_processor,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )
    yield
    structlog.reset_defaults()


def test_otel_processor__event_with_logger_name__emits_namespaced_record(
    otel_exporter: InMemoryLogExporter,
) -> None:
    # Given / When
    structlog.get_logger("code_references").info(
        "scan.created",
        organisation__id=42,
        code_references__count=3,
    )

    # Then
    records = otel_exporter.get_finished_logs()
    assert len(records) == 1

    log_record = records[0].log_record
    assert log_record.body == "scan.created"
    assert log_record.event_name == "code_references.scan.created"
    assert log_record.severity_number == SeverityNumber.INFO
    assert log_record.attributes is not None
    assert log_record.attributes["organisation.id"] == 42
    assert log_record.attributes["code_references.count"] == 3
    assert "event" not in log_record.attributes
    assert "level" not in log_record.attributes
    assert "timestamp" not in log_record.attributes
    assert "logger" not in log_record.attributes


def test_otel_processor__kebab_case_event__normalises_to_underscores(
    otel_exporter: InMemoryLogExporter,
) -> None:
    # Given / When
    structlog.get_logger("code_references").info("scan-created")

    # Then
    log_record = otel_exporter.get_finished_logs()[0].log_record
    assert log_record.body == "scan-created"
    assert log_record.event_name == "code_references.scan_created"


def test_otel_processor__no_explicit_logger_name__uses_module_name_as_prefix(
    otel_exporter: InMemoryLogExporter,
) -> None:
    # Given / When
    structlog.get_logger().info("some-event")

    # Then
    log_record = otel_exporter.get_finished_logs()[0].log_record
    assert log_record.body == "some-event"
    # structlog's add_logger_name derives the logger name from the calling module
    assert log_record.event_name == f"{__name__}.some_event"


def test_otel_processor__dunder_attributes__converts_to_dots(
    otel_exporter: InMemoryLogExporter,
) -> None:
    # Given / When
    structlog.get_logger().info(
        "test",
        organisation__id=1,
        feature__count=5,
        code_references__count=3,
    )

    # Then
    attrs = otel_exporter.get_finished_logs()[0].log_record.attributes
    assert attrs is not None
    assert attrs["organisation.id"] == 1
    assert attrs["feature.count"] == 5
    assert attrs["code_references.count"] == 3


def test_otel_processor__single_underscore_attributes__left_unchanged(
    otel_exporter: InMemoryLogExporter,
) -> None:
    # Given / When
    structlog.get_logger().info(
        "test",
        simple_attr="value",
        issues_created_count=7,
    )

    # Then
    attrs = otel_exporter.get_finished_logs()[0].log_record.attributes
    assert attrs is not None
    assert attrs["simple_attr"] == "value"
    assert attrs["issues_created_count"] == 7


def test_otel_processor__non_primitive_attributes__serialises_to_json(
    otel_exporter: InMemoryLogExporter,
) -> None:
    # Given / When
    structlog.get_logger().info(
        "test-event",
        nested={"key": "value"},
        items=[1, 2, 3],
    )

    # Then
    attrs = otel_exporter.get_finished_logs()[0].log_record.attributes
    assert attrs is not None
    assert attrs["nested"] == '{"key": "value"}'
    assert attrs["items"] == "[1, 2, 3]"


@pytest.mark.parametrize(
    "method, expected_severity",
    [
        ("debug", SeverityNumber.DEBUG),
        ("info", SeverityNumber.INFO),
        ("warning", SeverityNumber.WARN),
        ("error", SeverityNumber.ERROR),
        ("critical", SeverityNumber.FATAL),
    ],
)
def test_otel_processor__severity_level__maps_correctly(
    otel_exporter: InMemoryLogExporter,
    method: str,
    expected_severity: SeverityNumber,
) -> None:
    # Given / When
    getattr(structlog.get_logger(), method)("test")

    # Then
    log_record = otel_exporter.get_finished_logs()[0].log_record
    assert log_record.severity_number == expected_severity


def test_otel_processor__w3c_baggage__propagated_to_attributes(
    otel_exporter: InMemoryLogExporter,
) -> None:
    # Given
    ctx = baggage.set_baggage("amplitude.device_id", "device-123")
    ctx = baggage.set_baggage("amplitude.session_id", "session-456", context=ctx)

    # When
    token = context.attach(ctx)
    try:
        structlog.get_logger().info("test")
    finally:
        context.detach(token)

    # Then
    attrs = otel_exporter.get_finished_logs()[0].log_record.attributes
    assert attrs is not None
    assert attrs["amplitude.device_id"] == "device-123"
    assert attrs["amplitude.session_id"] == "session-456"


def test_build_otel_log_provider__valid_args__returns_configured_provider() -> None:
    # Given / When
    provider = build_otel_log_provider(
        endpoint="http://localhost:4318/v1/logs",
        service_name="test-service",
    )

    # Then
    assert isinstance(provider, LoggerProvider)
    assert provider.resource.attributes["service.name"] == "test-service"


def test_build_tracer_provider__valid_args__returns_configured_provider() -> None:
    # Given / When
    provider = build_tracer_provider(
        endpoint="http://localhost:4318/v1/traces",
        service_name="test-service",
    )

    # Then
    assert isinstance(provider, TracerProvider)
    assert provider.resource.attributes["service.name"] == "test-service"
