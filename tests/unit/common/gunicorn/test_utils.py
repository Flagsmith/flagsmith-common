import os
import signal
import threading
import time

import pytest
import pytest_mock

from common.gunicorn.utils import (
    DjangoWSGIApplication,
    run_server,
)


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
