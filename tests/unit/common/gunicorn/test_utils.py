import os
import signal
import threading
import time
from collections.abc import Generator
from importlib import reload

import pytest
from drf_spectacular.generators import EndpointEnumerator
from pytest_mock import MockerFixture

import common.gunicorn.utils
from common.gunicorn.utils import (
    DjangoWSGIApplication,
    get_route_template,
    run_server,
)


def test_django_wsgi_application__defaults__expected_config(
    mocker: MockerFixture,
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
    assert settings["keepalive"].value == 2
    assert settings["threads"].value == 1
    assert settings["timeout"].value == 30
    assert settings["workers"].value == 1
    assert app.load_wsgiapp() == wsgi_handler_mock


@pytest.fixture
def reload_gunicorn_utils() -> Generator[None, None, None]:
    yield
    reload(common.gunicorn.utils)


@pytest.mark.usefixtures("reload_gunicorn_utils")
def test_django_wsgi_application__env_vars_set__expected_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("GUNICORN_KEEP_ALIVE", "65")
    monkeypatch.setenv("GUNICORN_THREADS", "2")
    monkeypatch.setenv("GUNICORN_TIMEOUT", "60")
    monkeypatch.setenv("GUNICORN_WORKERS", "3")
    utils = reload(common.gunicorn.utils)

    # When
    app = utils.DjangoWSGIApplication({})

    # Then
    settings = app.cfg.settings
    assert settings["keepalive"].value == 65
    assert settings["threads"].value == 2
    assert settings["timeout"].value == 60
    assert settings["workers"].value == 3


def test_django_wsgi_application__gunicorn_cmd_args_set__overrides_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("GUNICORN_CMD_ARGS", "--keep-alive 65 --workers 4")

    # When
    app = DjangoWSGIApplication({})

    # Then
    settings = app.cfg.settings
    assert settings["keepalive"].value == 65
    assert settings["workers"].value == 4
    assert settings["config"].value == "python:common.gunicorn.conf"


def test_django_wsgi_application__gunicorn_cmd_args_and_options_set__options_take_precedence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("GUNICORN_CMD_ARGS", "--keep-alive 65 --workers 4")

    # When
    app = DjangoWSGIApplication({"keepalive": 10})

    # Then
    settings = app.cfg.settings
    assert settings["keepalive"].value == 10
    assert settings["workers"].value == 4


def test_run_server__default_config_file__runs_expected(
    unused_tcp_port: int,
    mocker: MockerFixture,
) -> None:
    # Given
    # prevent real forking from Gunicorn
    mocker.patch("os.fork").return_value = 0

    pid = os.getpid()

    def delay_kill(pid: int = pid) -> None:
        time.sleep(0.1)
        os.kill(pid, signal.SIGTERM)

    threading.Thread(target=delay_kill).start()

    # When / Then
    with pytest.raises(SystemExit):
        run_server({"bind": f"0.0.0.0:{unused_tcp_port}"})


def test_get_route_template__returns_expected__caches_expected(
    mocker: MockerFixture,
) -> None:
    # Given
    get_path_from_regex_spy = mocker.spy(EndpointEnumerator, "get_path_from_regex")
    regex_route = "^api/v1/environments/(?P<environment_api_key>[^/.]+)/api-keys/$"

    # When
    result = get_route_template(regex_route)
    get_route_template(regex_route)

    # Then
    assert result == "/api/v1/environments/{environment_api_key}/api-keys/"
    get_path_from_regex_spy.assert_called_once()
