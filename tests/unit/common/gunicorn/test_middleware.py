from common.core.request_context import RequestContextMiddleware
from common.gunicorn.middleware import RouteLoggerMiddleware


def test_route_logger_middleware__deprecated__is_request_context_middleware() -> None:
    # Given / When
    is_alias = issubclass(RouteLoggerMiddleware, RequestContextMiddleware)

    # Then
    assert is_alias
