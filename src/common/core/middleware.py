from typing import Callable

from django.http import HttpRequest, HttpResponse

from common.core.utils import get_version


class APIResponseVersionHeaderMiddleware:
    """
    Middleware to add the API version to the response headers
    """

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response.headers["Flagsmith-Version"] = get_version()
        return response
