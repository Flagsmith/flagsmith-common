import logging
import sys
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from django.conf import settings
from gunicorn.config import Config  # type: ignore[import-untyped]
from gunicorn.http.message import Request  # type: ignore[import-untyped]
from gunicorn.http.wsgi import Response  # type: ignore[import-untyped]
from gunicorn.instrument.statsd import (  # type: ignore[import-untyped]
    Statsd as StatsdGunicornLogger,
)

from common.core.logging import JsonFormatter
from common.gunicorn import metrics
from common.gunicorn.constants import WSGI_DJANGO_ROUTE_ENVIRON_KEY


class GunicornAccessLogJsonFormatter(JsonFormatter):
    def get_json_record(self, record: logging.LogRecord) -> dict[str, Any]:
        args = record.args

        if TYPE_CHECKING:
            assert isinstance(args, dict)

        url = args["U"]
        if q := args["q"]:
            url += f"?{q}"

        return {
            **super().get_json_record(record),
            "time": datetime.strptime(args["t"], "[%d/%b/%Y:%H:%M:%S %z]").isoformat(),
            "path": url,
            "remote_ip": args["h"],
            "route": args["R"],
            "method": args["m"],
            "status": str(args["s"]),
            "user_agent": args["a"],
            "duration_in_ms": args["M"],
        }


class PrometheusGunicornLogger(StatsdGunicornLogger):  # type: ignore[misc]
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
            "route": environ.get(WSGI_DJANGO_ROUTE_ENVIRON_KEY) or "",
            "method": environ.get("REQUEST_METHOD") or "",
            "response_status": resp.status_code,
        }
        metrics.flagsmith_http_server_request_duration_seconds.labels(**labels).observe(
            duration_seconds
        )
        metrics.flagsmith_http_server_requests_total.labels(**labels).inc()


class GunicornJsonCapableLogger(PrometheusGunicornLogger):
    def atoms(
        self,
        resp: Response,
        req: Request,
        environ: dict[str, Any],
        request_time: timedelta,
    ) -> dict[str, str]:
        atoms: dict[str, str] = super().atoms(resp, req, environ, request_time)
        atoms["R"] = environ.get(WSGI_DJANGO_ROUTE_ENVIRON_KEY) or "-"
        return atoms

    def setup(self, cfg: Config) -> None:
        super().setup(cfg)
        if getattr(settings, "LOG_FORMAT", None) == "json":
            self._set_handler(
                self.error_log,
                cfg.errorlog,
                JsonFormatter(),
            )
            self._set_handler(
                self.access_log,
                cfg.accesslog,
                GunicornAccessLogJsonFormatter(),
                stream=sys.stdout,
            )
