import logging
import os
from datetime import timedelta
from typing import Any

from gunicorn.config import Config  # type: ignore[import-untyped]
from gunicorn.http.message import Request  # type: ignore[import-untyped]
from gunicorn.http.wsgi import Response  # type: ignore[import-untyped]
from gunicorn.instrument.statsd import (  # type: ignore[import-untyped]
    Statsd as StatsdGunicornLogger,
)

from common.gunicorn import metrics
from common.gunicorn.utils import get_extra


class PrometheusGunicornLogger(StatsdGunicornLogger):  # type: ignore[misc]
    """Gunicorn logger that records Prometheus metrics on each access log entry."""

    def access(
        self,
        resp: Response,
        req: Request,
        environ: dict[str, Any],
        request_time: timedelta,
    ) -> None:
        super().access(resp, req, environ, request_time)
        duration_seconds = (
            request_time.seconds + float(request_time.microseconds) / 10**6
        )
        labels = {
            # To avoid cardinality explosion, we use a resolved Django route
            # instead of raw path.
            # The Django route is set by `RouteLoggerMiddleware`.
            "route": get_extra(environ=environ, key="route") or "",
            "method": environ.get("REQUEST_METHOD") or "",
            "response_status": resp.status_code,
        }
        metrics.flagsmith_http_server_request_duration_seconds.labels(**labels).observe(
            duration_seconds
        )
        metrics.flagsmith_http_server_requests_total.labels(**labels).inc()
        metrics.flagsmith_http_server_response_size_bytes.labels(**labels).observe(
            getattr(resp, "sent", 0),
        )


class GunicornJsonCapableLogger(PrometheusGunicornLogger):
    """Gunicorn logger that integrates with the application logging setup."""

    def setup(self, cfg: Config) -> None:
        super().setup(cfg)

        # Error log always propagates to root.
        for handler in self.error_log.handlers[:]:
            self.error_log.removeHandler(handler)
        self.error_log.propagate = True

        # In JSON mode, replace the access log formatter with the root's
        # ProcessorFormatter. In generic mode, keep Gunicorn's CLF formatter.
        # The handler itself is preserved so ACCESS_LOG_LOCATION is respected.
        root_handlers = logging.getLogger().handlers
        if os.environ.get("LOG_FORMAT") == "json" and root_handlers:
            root_formatter = root_handlers[0].formatter
            for handler in self.access_log.handlers:
                handler.setFormatter(root_formatter)
