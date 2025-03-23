import argparse
from typing import Any

from django.core.handlers.wsgi import WSGIHandler
from django.core.wsgi import get_wsgi_application
from environs import Env
from gunicorn.app.wsgiapp import (  # type: ignore[import-untyped]
    WSGIApplication as GunicornWSGIApplication,
)
from gunicorn.config import Config  # type: ignore[import-untyped]

env = Env()

DEFAULT_ACCESS_LOG_FORMAT = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %({origin}i)s %({access-control-allow-origin}o)s'
GUNICORN_FLAGSMITH_DEFAULTS = {
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
            for key, value in {**GUNICORN_FLAGSMITH_DEFAULTS, **self.options}.items()
            if key in cfg_settings
        )
        for key, value in options_items:
            print(f"setting {key=} {value=}")
            self.cfg.set(key.lower(), value)
        self.load_config_from_module_name_or_filename(self.cfg.config)

    def load_wsgiapp(self) -> WSGIHandler:
        return get_wsgi_application()


def add_arguments(parser: argparse._ArgumentGroup) -> None:
    _config = Config()
    keys = sorted(_config.settings, key=_config.settings.__getitem__)
    for key in keys:
        _config.settings[key].add_option(parser)


def run_server(options: dict[str, Any] | None = None) -> None:
    DjangoWSGIApplication(options).run()
