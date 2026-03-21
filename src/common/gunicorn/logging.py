import logging
import os
from datetime import datetime, timedelta
from typing import Any

from gunicorn.config import Config  # type: ignore[import-untyped]
from gunicorn.http.message import Request  # type: ignore[import-untyped]
from gunicorn.http.wsgi import Response  # type: ignore[import-untyped]
from gunicorn.instrument.statsd import (  # type: ignore[import-untyped]
    Statsd as StatsdGunicornLogger,
)
from structlog.typing import EventDict, Processor, WrappedLogger

from common.gunicorn import metrics
from common.gunicorn.constants import (
    WSGI_EXTRA_SUFFIX_TO_CATEGORY,
    wsgi_extra_key_regex,
)
from common.gunicorn.utils import get_extra


def make_gunicorn_access_processor(
    access_log_extra_items: list[str] | None = None,
) -> Processor:
    """Create a processor that extracts structured fields from Gunicorn access logs.

    Gunicorn populates ``record.args`` with a dict of request/response data
    (keyed by format variables like ``h``, ``m``, ``s``, ``U``, etc.).  This
    processor detects those records and promotes the data into the event dict
    so it flows through the normal rendering pipeline.

    Pass the returned processor to :func:`~common.core.logging.setup_logging`
    via ``extra_foreign_processors``.
    """

    def processor(
        logger: WrappedLogger,
        method_name: str,
        event_dict: EventDict,
    ) -> EventDict:
        record = event_dict.get("_record")
        if record is None or record.name != "gunicorn.access":
            return event_dict
        # ProcessorFormatter clears record.args before running
        # foreign_pre_chain; the originals are stashed on the record
        # by _SentryFriendlyProcessorFormatter.format().
        args = getattr(record, "_original_args", record.args)
        if not isinstance(args, dict):
            return event_dict

        url = args.get("U", "")
        if q := args.get("q"):
            url += f"?{q}"

        if t := args.get("t"):
            event_dict["time"] = datetime.strptime(
                t, "[%d/%b/%Y:%H:%M:%S %z]"
            ).isoformat()
        event_dict["path"] = url
        event_dict["remote_ip"] = args.get("h", "")
        event_dict["method"] = args.get("m", "")
        event_dict["status"] = str(args.get("s", ""))
        event_dict["user_agent"] = args.get("a", "")
        event_dict["duration_in_ms"] = args.get("M", 0)
        event_dict["response_size_in_bytes"] = args.get("B") or 0

        if access_log_extra_items:
            for extra_key in access_log_extra_items:
                extra_key_lower = extra_key.lower()
                if (
                    (extra_value := args.get(extra_key_lower))
                    and (re_match := wsgi_extra_key_regex.match(extra_key_lower))
                    and (
                        category := WSGI_EXTRA_SUFFIX_TO_CATEGORY.get(
                            re_match.group("suffix")
                        )
                    )
                ):
                    event_dict.setdefault(category, {})[re_match.group("key")] = (
                        extra_value
                    )

        return event_dict

    return processor


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
        if os.environ.get("LOG_FORMAT") == "json":
            root_formatter = logging.getLogger().handlers[0].formatter
            for handler in self.access_log.handlers:
                handler.setFormatter(root_formatter)
