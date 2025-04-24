import json
import logging
import logging.config
import os

import pytest

from common.core.logging import JsonFormatter


@pytest.mark.freeze_time("2023-12-08T06:05:47.320000+00:00")
def test_json_formatter__outputs_expected(
    caplog: pytest.LogCaptureFixture,
    request: pytest.FixtureRequest,
) -> None:
    # Given
    json_formatter = JsonFormatter()

    caplog.handler.setFormatter(json_formatter)
    logger = logging.getLogger("test_json_formatter__outputs_expected")
    logger.setLevel(logging.INFO)

    expected_pid = os.getpid()
    expected_module_path = os.path.abspath(request.path)
    expected_tb_string = (
        "Traceback (most recent call last):\n"
        f'  File "{expected_module_path}",'
        " line 34, in _log_traceback\n"
        "    raise Exception()\nException"
    )

    def _log_traceback() -> None:
        try:
            raise Exception()
        except Exception as exc:
            logger.error("this is an error", exc_info=exc)

    # When
    logger.info("hello %s, %d", "arg1", 22.22)
    _log_traceback()

    # Then
    assert [json.loads(message) for message in caplog.text.split("\n") if message] == [
        {
            "levelname": "INFO",
            "message": "hello arg1, 22",
            "timestamp": "2023-12-08 06:05:47,320",
            "logger_name": "test_json_formatter__outputs_expected",
            "pid": expected_pid,
            "thread_name": "MainThread",
        },
        {
            "levelname": "ERROR",
            "message": "this is an error",
            "timestamp": "2023-12-08 06:05:47,320",
            "logger_name": "test_json_formatter__outputs_expected",
            "pid": expected_pid,
            "thread_name": "MainThread",
            "exc_info": expected_tb_string,
        },
    ]
