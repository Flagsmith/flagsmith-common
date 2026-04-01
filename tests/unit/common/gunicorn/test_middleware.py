from typing import Any

import pytest
from django.http import HttpRequest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from pytest_mock import MockerFixture

from common.gunicorn.middleware import RouteLoggerMiddleware


@pytest.fixture()
def span_exporter() -> tuple[InMemorySpanExporter, TracerProvider]:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return exporter, provider


def test_route_logger_middleware__resolved_route__sets_log_extra_and_span_name(
    mocker: MockerFixture,
    span_exporter: tuple[InMemorySpanExporter, TracerProvider],
) -> None:
    # Given
    exporter, provider = span_exporter
    tracer = provider.get_tracer(__name__)

    request = mocker.Mock(spec=HttpRequest)
    request.method = "GET"
    request.resolver_match = mocker.Mock()
    request.resolver_match.route = "api/v1/projects/<int:pk>/"
    request.META = {}

    response = mocker.Mock()

    def get_response(req: object) -> Any:
        return response

    middleware = RouteLoggerMiddleware(get_response)

    # When
    with tracer.start_as_current_span("original"):
        result = middleware(request)

    # Then
    assert result is response
    assert request.META["flagsmith.route"] == "/api/v1/projects/{pk}/"
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "GET /api/v1/projects/{pk}/"


def test_route_logger_middleware__no_resolver_match__no_log_extra_and_span_unchanged(
    mocker: MockerFixture,
    span_exporter: tuple[InMemorySpanExporter, TracerProvider],
) -> None:
    # Given
    exporter, provider = span_exporter
    tracer = provider.get_tracer(__name__)

    request = mocker.Mock(spec=HttpRequest)
    request.resolver_match = None
    request.META = {}

    response = mocker.Mock()
    middleware = RouteLoggerMiddleware(mocker.Mock(return_value=response))

    # When
    with tracer.start_as_current_span("original"):
        middleware(request)

    # Then
    assert "flagsmith.route" not in request.META
    spans = exporter.get_finished_spans()
    assert spans[0].name == "original"


def test_route_logger_middleware__no_active_span__sets_log_extra(
    mocker: MockerFixture,
) -> None:
    # Given
    request = mocker.Mock(spec=HttpRequest)
    request.resolver_match = mocker.Mock()
    request.resolver_match.route = "version/"
    request.method = "GET"
    request.META = {}

    response = mocker.Mock()
    middleware = RouteLoggerMiddleware(mocker.Mock(return_value=response))

    # When
    result = middleware(request)

    # Then
    assert result is response
    assert request.META["flagsmith.route"] == "/version/"
