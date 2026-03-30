from typing import Callable

from django.http import HttpRequest, HttpResponse
from opentelemetry import trace

from common.gunicorn.utils import get_route_template, log_extra


class RouteLoggerMiddleware:
    """
    Make the resolved Django route available to the WSGI server
    (e.g. Gunicorn) for logging and tracing purposes.
    """

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if resolver_match := request.resolver_match:
            route_template = get_route_template(resolver_match.route)
            log_extra(
                request=request,
                key="route",
                value=route_template,
            )
            span = trace.get_current_span()
            if span.is_recording():
                span.update_name(f"{request.method} {route_template}")

        return response
