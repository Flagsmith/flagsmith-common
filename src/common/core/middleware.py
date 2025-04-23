from typing import Callable

from django.http import HttpRequest, HttpResponse

from common.core.utils import UNKNOWN, get_versions_from_manifest


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
        response.headers["X-Flagsmith-Version"] = self.get_version()
        return response
    
    def get_version(self) -> str:
        """Obtains the version number from the manifest file"""
        manifest_versions = get_versions_from_manifest()
        version: str = manifest_versions.get(".") or UNKNOWN
        return version
