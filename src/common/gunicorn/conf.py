"""
This module is used as a default configuration file for Gunicorn.

It is used to correctly support Prometheus metrics in a multi-process environment.
"""

import os
import typing

from prometheus_client.multiprocess import mark_process_dead

if typing.TYPE_CHECKING:  # pragma: no cover
    from gunicorn.arbiter import Arbiter  # type: ignore[import-untyped]
    from gunicorn.workers.base import Worker  # type: ignore[import-untyped]


def when_ready(server: "Arbiter") -> None:
    """Start the standalone Prometheus metrics server after Gunicorn is ready."""
    prometheus_enabled = os.getenv("PROMETHEUS_ENABLED", "")
    if prometheus_enabled.lower() == "true":  # Django settings are not available
        from common.gunicorn.metrics_server import start_metrics_server

        start_metrics_server()


def child_exit(server: "Arbiter", worker: "Worker") -> None:
    """Detach the process Prometheus metrics collector when a worker exits."""
    mark_process_dead(worker.pid)  # type: ignore[no-untyped-call]
