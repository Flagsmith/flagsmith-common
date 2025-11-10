"""
This module is used as a default configuration file for Gunicorn.

It is used to correctly support Prometheus metrics in a multi-process environment.
"""

import typing

from prometheus_client.multiprocess import mark_process_dead

if typing.TYPE_CHECKING:  # pragma: no cover
    from gunicorn.arbiter import Arbiter  # type: ignore[import-untyped]
    from gunicorn.workers.base import Worker  # type: ignore[import-untyped]


def worker_exit(server: "Arbiter", worker: "Worker") -> None:
    """Detach the process Prometheus metrics collector when a worker exits."""
    mark_process_dead(worker.pid)  # type: ignore[no-untyped-call]
