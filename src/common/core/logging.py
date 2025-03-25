import json
import logging
from typing import Any


class JsonFormatter(logging.Formatter):
    """Custom formatter for json logs."""

    def get_json_record(self, record: logging.LogRecord) -> dict[str, Any]:
        formatted_message = record.getMessage()
        json_record = {
            "levelname": record.levelname,
            "message": formatted_message,
            "timestamp": self.formatTime(record, self.datefmt),
            "logger_name": record.name,
            "pid": record.process,
            "thread_name": record.threadName,
        }
        if record.exc_info:
            json_record["exc_info"] = self.formatException(record.exc_info)
        return json_record

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(self.get_json_record(record))
