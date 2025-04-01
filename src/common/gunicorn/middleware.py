from typing import Callable

from django.http import HttpRequest, HttpResponse

from common.gunicorn.constants import WSGI_DJANGO_ROUTE_ENVIRON_KEY
from common.gunicorn.utils import get_route_template


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
            # https://peps.python.org/pep-3333/#specification-details
            # "...the application is allowed to modify the dictionary in any way it desires"
            request.META[WSGI_DJANGO_ROUTE_ENVIRON_KEY] = get_route_template(
                resolver_match.route
            )

        return response
