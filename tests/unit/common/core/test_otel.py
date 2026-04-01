from typing import Generator

import pytest
import pytest_mock
import structlog
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
    setup_tracing,
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


def test_otel_processor__active_span__adds_span_event(
    otel_exporter: InMemoryLogExporter,
) -> None:
    # Given
    provider = TracerProvider()
    tracer = provider.get_tracer(__name__)

    # When
    with tracer.start_as_current_span("test-span") as span:
        structlog.get_logger("mylogger").info("something-happened", detail="value")

    # Then — span event is added with the same name and attributes
    events = span.events  # type: ignore[attr-defined]
    assert len(events) == 1
    assert events[0].name == "mylogger.something_happened"
    assert events[0].attributes is not None
    assert events[0].attributes["detail"] == "value"


def test_otel_processor__no_active_span__no_span_event(
    otel_exporter: InMemoryLogExporter,
) -> None:
    # Given / When — no active span
    structlog.get_logger("mylogger").info("no-span-event")

    # Then — log record is still emitted
    records = otel_exporter.get_finished_logs()
    assert len(records) == 1
    assert records[0].log_record.body == "no-span-event"


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


def test_setup_tracing__called__instruments_and_uninstruments_all_libraries(
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Given
    mocker.patch("common.core.otel.DjangoInstrumentor.instrument")
    mocker.patch("common.core.otel.DjangoInstrumentor.uninstrument")
    psycopg2_instrument = mocker.patch(
        "common.core.otel.Psycopg2Instrumentor.instrument"
    )
    psycopg2_uninstrument = mocker.patch(
        "common.core.otel.Psycopg2Instrumentor.uninstrument"
    )
    redis_instrument = mocker.patch("common.core.otel.RedisInstrumentor.instrument")
    redis_uninstrument = mocker.patch("common.core.otel.RedisInstrumentor.uninstrument")
    provider = TracerProvider()

    # When
    with setup_tracing(provider):
        psycopg2_instrument.assert_called_once_with(
            enable_commenter=True, skip_dep_check=True
        )
        redis_instrument.assert_called_once()

    # Then — uninstrumented on exit
    psycopg2_uninstrument.assert_called_once()
    redis_uninstrument.assert_called_once()
