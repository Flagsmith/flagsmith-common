from collections.abc import Generator

import pytest
import structlog.contextvars
from django.http import HttpRequest, HttpResponse
from django.test import Client, RequestFactory
from django.urls import resolve
from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from common.core import request_context
from common.core.request_context import (
    RequestContextMiddleware,
    bind_request_context,
    get_request_context,
)


@pytest.fixture(autouse=True)
def clean_contextvars() -> Generator[None, None, None]:
    structlog.contextvars.clear_contextvars()
    yield
    structlog.contextvars.clear_contextvars()


def test_bind_request_context__attributes__returned_by_get_request_context() -> None:
    # Given / When
    bind_request_context(organisation__id=1, http__route="/version/")

    # Then
    assert get_request_context("organisation__id") == 1
    assert get_request_context("http__route") == "/version/"
    assert get_request_context("project__id") is None


def test_bind_request_context__attributes__merged_into_structlog_events() -> None:
    # Given
    bind_request_context(organisation__id=1)

    # When
    event_dict = structlog.contextvars.merge_contextvars(None, "info", {"event": "x"})

    # Then
    assert event_dict == {"event": "x", "organisation__id": 1}


def test_bind_request_context__recording_span__sets_dotted_span_attributes(
    span_exporter: InMemorySpanExporter,
) -> None:
    # Given
    tracer = trace.get_tracer(__name__)

    # When
    with tracer.start_as_current_span("request"):
        bind_request_context(organisation__id=1, http__route="/version/")

    # Then
    [span] = span_exporter.get_finished_spans()
    assert span.attributes == {"organisation.id": 1, "http.route": "/version/"}


def test_bind_request_context__no_recording_span__binds_context_only() -> None:
    # Given / When
    with trace.use_span(trace.INVALID_SPAN):
        bind_request_context(organisation__id=1)

    # Then
    assert get_request_context("organisation__id") == 1


def test_request_context_middleware__process_view__binds_openapi_route_and_method(
    rf: RequestFactory,
) -> None:
    # Given
    request = rf.get("/version/")
    request.resolver_match = resolve("/version/")
    middleware = RequestContextMiddleware(lambda request: HttpResponse())

    # When
    middleware.process_view(request, request.resolver_match.func, (), {})

    # Then
    assert get_request_context("http__route") == "/version/"
    assert get_request_context("http__request__method") == "GET"


def test_request_context_middleware__bound_while_handling__not_visible_after(
    rf: RequestFactory,
) -> None:
    # Given
    bind_request_context(deployment__environment="test")
    seen: dict[str, object] = {}

    def get_response(request: HttpRequest) -> HttpResponse:
        seen["outer"] = get_request_context("deployment__environment")
        bind_request_context(organisation__id=1)
        return HttpResponse()

    middleware = RequestContextMiddleware(get_response)

    # When
    middleware(rf.get("/version/"))

    # Then
    assert seen == {"outer": "test"}  # Context bound outside is visible inside
    assert get_request_context("organisation__id") is None
    assert get_request_context("deployment__environment") == "test"  # Not cleared


def test_request_context_middleware__consecutive_requests__context_does_not_leak(
    rf: RequestFactory,
) -> None:
    # Given
    seen: list[object] = []

    def get_response(request: HttpRequest) -> HttpResponse:
        seen.append(get_request_context("organisation__id"))
        if request.GET.get("org"):
            bind_request_context(organisation__id=int(request.GET["org"]))
        return HttpResponse()

    middleware = RequestContextMiddleware(get_response)

    # When
    middleware(rf.get("/version/", {"org": "1"}))
    middleware(rf.get("/version/"))

    # Then
    assert seen == [None, None]


def test_request_context_middleware__django_request__binds_route_for_the_view(
    client: Client,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.MIDDLEWARE = ["common.core.request_context.RequestContextMiddleware"]
    bind_spy = mocker.spy(request_context, "bind_request_context")

    # When
    response = client.get("/health/liveness/")

    # Then
    assert response.status_code == 200
    bind_spy.assert_called_once_with(
        http__request__method="GET",
        http__route="/health/liveness/",
    )
