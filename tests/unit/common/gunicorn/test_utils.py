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


def test_run_server__default_config_file__runs_expected(
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Given
    # prevent real forking from Gunicorn
    mocker.patch("os.fork").return_value = 0
    mark_process_dead_mock = mocker.patch("common.gunicorn.conf.mark_process_dead")

    def delay_kill(pid: int = os.getpid()) -> None:
        time.sleep(0.1)
        os.kill(pid, signal.SIGTERM)

    threading.Thread(target=delay_kill).start()

    # When
    with pytest.raises(SystemExit):
        run_server()

    # Then
    mark_process_dead_mock.assert_called()
