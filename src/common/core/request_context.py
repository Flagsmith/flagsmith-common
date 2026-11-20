"""
Request-scoped telemetry context.

Attributes bound here describe the request being handled, e.g. the
organisation it acts on, and reach every telemetry signal without call sites
passing them along:

- structlog events, via the `merge_contextvars` processor;
- the current OpenTelemetry span, as span attributes.

Name attributes like structlog event kwargs, e.g. `organisation__id`; they are
reported as `organisation.id`. `RequestContextMiddleware` scopes bindings to
the request.
"""

import contextvars
from collections.abc import Callable
from typing import Any

import structlog.contextvars
from django.http import HttpRequest, HttpResponse
from opentelemetry import trace
from opentelemetry.util.types import AttributeValue

from common.gunicorn.utils import get_route_template, log_extra


def bind_request_context(**attributes: AttributeValue) -> None:
    """Describe the current request with `attributes`, e.g. `organisation__id=1`."""
    structlog.contextvars.bind_contextvars(**attributes)
    span = trace.get_current_span()
    if span.is_recording():
        span.set_attributes(
            {name.replace("__", "."): value for name, value in attributes.items()}
        )


def get_request_context(name: str) -> Any:
    """Return the value bound to `name` for the current request, if any."""
    return structlog.contextvars.get_contextvars().get(name)


class RequestContextMiddleware:
    """
    Scope request context to the request, and record its route.

    The route, in its OpenAPI schema form, is bound to the request context,
    names the current span, and is passed on to Gunicorn's access log and
    HTTP metrics through the WSGI `environ`.

    Put it before any middleware that binds request context, and before any
    middleware whose `process_view` can return a response, e.g.
    `CsrfViewMiddleware`, so the route is recorded for every resolved request.
    """

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Handle the request in a copy of the current context, so whatever
        # gets bound while handling it doesn't leak into the next request
        # served by the same thread.
        return contextvars.copy_context().run(self.get_response, request)

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., HttpResponse],
        view_args: tuple[Any, ...],
        view_kwargs: dict[str, Any],
    ) -> None:
        # The URL is resolved by now.
        assert request.resolver_match
        route = get_route_template(
            request.resolver_match.route,
            getattr(view_func, "cls", None),
        )
        bind_request_context(
            http__request__method=request.method or "",
            http__route=route,
        )
        # Gunicorn logs requests after they leave Django, and this context
        log_extra(request=request, key="route", value=route)
        span = trace.get_current_span()
        if span.is_recording():
            span.update_name(f"{request.method} {route}")
