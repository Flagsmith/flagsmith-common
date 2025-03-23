import logging
import sys
from datetime import datetime, timedelta
from typing import Any

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
from common.gunicorn.utils import get_status_from_wsgi_response_status
from common.prometheus.utils import with_labels


class GunicornAccessLogJsonFormatter(JsonFormatter):
    def get_json_record(self, record: logging.LogRecord) -> dict[str, Any]:
        args = record.args
        url = args["U"]  # type: ignore[call-overload,index]
        if q := args["q"]:  # type: ignore[call-overload,index]
            url += f"?{q}"  # type: ignore[operator]

        return {
            **super().get_json_record(record),
            "time": datetime.strptime(args["t"], "[%d/%b/%Y:%H:%M:%S %z]").isoformat(),  # type: ignore[arg-type,call-overload,index]  # noqa: E501
            "path": url,
            "remote_ip": args["h"],  # type: ignore[call-overload,index]
            "method": args["m"],  # type: ignore[call-overload,index]
            "status": str(args["s"]),  # type: ignore[call-overload,index]
            "user_agent": args["a"],  # type: ignore[call-overload,index]
            "referer": args["f"],  # type: ignore[call-overload,index]
            "duration_in_ms": args["M"],  # type: ignore[call-overload,index]
            "pid": args["p"],  # type: ignore[call-overload,index]
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
            # The Django route is set by `PrometheusGunicornLoggerMiddleware`.
            "path": environ.get(WSGI_DJANGO_ROUTE_ENVIRON_KEY),
            "method": environ.get("REQUEST_METHOD"),
            "response_status": get_status_from_wsgi_response_status(resp.status),
        }
        with_labels(metrics.http_request_duration_seconds, **labels).observe(
            duration_seconds
        )
        with_labels(metrics.http_requests_total, **labels).inc()


class GunicornJsonCapableLogger(PrometheusGunicornLogger):
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
