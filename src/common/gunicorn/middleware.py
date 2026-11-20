from common.core.request_context import RequestContextMiddleware


class RouteLoggerMiddleware(RequestContextMiddleware):
    """
    Deprecated alias of `common.core.request_context.RequestContextMiddleware`,
    which now records the route for logs, metrics and traces.
    """
