from typing import Callable

from django.http import HttpRequest, HttpResponse

from common.gunicorn.utils import get_route_template, log_extra


class RouteLoggerMiddleware:
    """
    Make the resolved Django route available to the WSGI server
    (e.g. Gunicorn) for logging purposes.
    """

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if resolver_match := request.resolver_match:
            log_extra(
                request=request,
                key="route",
                value=get_route_template(resolver_match.route),
            )

        return response
