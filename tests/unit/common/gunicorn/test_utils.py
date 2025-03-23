import os
import signal
import threading
import time

import pytest
import pytest_mock

from common.gunicorn.utils import (
    DjangoWSGIApplication,
    get_status_from_wsgi_response_status,
    run_server,
)


@pytest.mark.parametrize(
    "status,expected",
    (
        [b" 200 ", "200"],
        [200, "200"],
        ["200", "200"],
        [None, "unknown"],
    ),
)
def test_get_status_from_wsgi_response_status__returns_expected(
    status: str | bytes | int | None,
    expected: str,
) -> None:
    # When
    result = get_status_from_wsgi_response_status(status)

    # Then
    assert result == expected


def test_django_wsgi_application__defaults__expected_config(
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Given
    wsgi_handler_mock = mocker.Mock()
    mocker.patch(
        "common.gunicorn.utils.get_wsgi_application",
        return_value=wsgi_handler_mock,
    )

    # When
    app = DjangoWSGIApplication({})

    # Then
    settings = app.cfg.settings
    assert (
        settings["logger_class"].value
        == "common.gunicorn.logging.GunicornJsonCapableLogger"
    )
    assert settings["config"].value == "python:common.gunicorn.conf"
    assert app.load_wsgiapp() == wsgi_handler_mock


def test_run_server__expected_config() -> None:
    # Given
    def delay_kill(pid: int = os.getpid()) -> None:
        time.sleep(0.1)
        os.kill(pid, signal.SIGTERM)

    threading.Thread(target=delay_kill).start()

    # When
    with pytest.raises(SystemExit):
        run_server()

    # Then
    from prometheus_client import multiprocess

    multiprocess.mark_process_dead
