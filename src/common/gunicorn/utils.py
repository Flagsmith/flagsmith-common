import argparse
from functools import lru_cache
from typing import Any

from django.core.handlers.wsgi import WSGIHandler
from django.core.wsgi import get_wsgi_application
from django.urls import Resolver404, resolve
from environs import Env
from gunicorn.app.wsgiapp import (  # type: ignore[import-untyped]
    WSGIApplication as GunicornWSGIApplication,
)
from gunicorn.config import Config

from common.prometheus.constants import UNKNOWN_LABEL_VALUE
from common.prometheus.types import LabelValue

env = Env()

DEFAULT_ACCESS_LOG_FORMAT = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %({origin}i)s %({access-control-allow-origin}o)s'
DEFAULT_GUNICORN_SETTINGS = {
    "access_log_format": env.str("ACCESS_LOG_FORMAT", DEFAULT_ACCESS_LOG_FORMAT),
    "accesslog": env.str("ACCESS_LOG_LOCATION", "/dev/null"),
    "bind": "0.0.0.0:8000",
    "config": "python:common.gunicorn.conf",
    "logger_class": "common.gunicorn.logging.GunicornJsonCapableLogger",
    "statsd_prefix": "flagsmith.api",
    "threads": env.int("GUNICORN_THREADS", 1),
    "timeout": env.int("GUNICORN_TIMEOUT", 30),
    "worker_class": "sync",
    "workers": env.int("GUNICORN_WORKERS", 1),
}


class DjangoWSGIApplication(GunicornWSGIApplication):  # type: ignore[misc]
    def __init__(self, options: dict[str, Any] | None) -> None:
        self.options = {
            key: value for key, value in (options or {}).items() if value is not None
        }
        super().__init__()

    def load_config(self) -> None:
        cfg_settings = self.cfg.settings
        options_items = (
            (key, value)
            for key, value in {**DEFAULT_GUNICORN_SETTINGS, **self.options}.items()
            if key in cfg_settings and value is not None
        )
        for key, value in options_items:
            print(f"setting {key=} {value=}")
            self.cfg.set(key.lower(), value)
        self.load_config_from_module_name_or_filename(self.cfg.config)

    def load_wsgiapp(self) -> WSGIHandler:
        return get_wsgi_application()


@lru_cache(maxsize=64)
def get_status_from_wsgi_response_status(
    status: str | bytes | int | None,
) -> LabelValue:
    if isinstance(status, int):
        return str(status)
    if isinstance(status, bytes):
        status = status.decode("utf-8")
    if isinstance(status, str):
        status = status.split(None, 1)[0]
    return status or UNKNOWN_LABEL_VALUE


def get_route_from_wsgi_path_info(
    path_info: str | None,
) -> LabelValue:
    try:
        if path_info:
            return resolve(path_info).route
    except Resolver404:
        pass
    return UNKNOWN_LABEL_VALUE


def add_arguments(parser: argparse._ArgumentGroup) -> None:
    _config = Config()
    keys = sorted(_config.settings, key=_config.settings.__getitem__)
    for key in keys:
        _config.settings[key].add_option(parser)


def run_server(options: dict[str, Any] | None = None) -> None:
    DjangoWSGIApplication(options).run()
