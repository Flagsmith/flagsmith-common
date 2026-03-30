from datetime import datetime

from structlog.typing import EventDict, Processor, WrappedLogger

from common.gunicorn.constants import (
    WSGI_EXTRA_SUFFIX_TO_CATEGORY,
    wsgi_extra_key_regex,
)


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
        # ProcessorFormatter clears record.args on its internal copy
        # before running foreign_pre_chain; the originals are available
        # via pass_foreign_args=True as "positional_args" in event_dict.
        args = event_dict.get("positional_args", record.args)
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
