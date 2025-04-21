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
from common.gunicorn.constants import (
    WSGI_EXTRA_PREFIX,
    WSGI_EXTRA_SUFFIX_TO_CATEGORY,
    wsgi_extra_key_regex,
)
from common.gunicorn.utils import get_extra


class GunicornAccessLogJsonFormatter(JsonFormatter):
    def _get_extra(self, record_args: dict[str, Any]) -> dict[str, Any]:
        ret: dict[str, dict[str, Any]] = {}

        extra_items_to_log: list[str] | None
        if extra_items_to_log := getattr(settings, "ACCESS_LOG_EXTRA_ITEMS", None):
            # We expect the extra items to be in the form of
            # Gunicorn's access log format string for
            # request headers, response headers and environ variables
            # without the % prefix, e.g. "{origin}i" or "{flagsmith.environment_id}e"
            # https://docs.gunicorn.org/en/stable/settings.html#access-log-format
            for extra_key in extra_items_to_log:
                extra_key_lower = extra_key.lower()
                if (
                    (extra_value := record_args.get(extra_key_lower))
                    and (re_match := wsgi_extra_key_regex.match(extra_key_lower))
                    and (
                        extra_category := WSGI_EXTRA_SUFFIX_TO_CATEGORY.get(
                            re_match.group("suffix")
                        )
                    )
                ):
                    ret.setdefault(extra_category, {})[re_match.group("key")] = (
                        extra_value
                    )

        return ret

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
            "route": args.get(f"{{{WSGI_EXTRA_PREFIX}route}}e") or "",
            "method": args["m"],
            "status": str(args["s"]),
            "user_agent": args["a"],
            "duration_in_ms": args["M"],
            "response_size_in_bytes": args["B"] or 0,
            **self._get_extra(args),
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
