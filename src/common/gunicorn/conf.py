"""
This module is used as a default configuration file for Gunicorn.

It is used to correctly support Prometheus metrics in a multi-process environment.
"""

import os
import pathlib
import shutil
import typing
from tempfile import gettempdir

from prometheus_client.multiprocess import mark_process_dead

from common.core.constants import DEFAULT_PROMETHEUS_MULTIPROC_DIR_NAME

if typing.TYPE_CHECKING:  # pragma: no cover
    from gunicorn.arbiter import Arbiter  # type: ignore[import-untyped]
    from gunicorn.workers.base import Worker  # type: ignore[import-untyped]


def worker_exit(server: "Arbiter", worker: "Worker") -> None:
    """Detach the process Prometheus metrics collector when a worker exits."""
    mark_process_dead(worker.pid)  # type: ignore[no-untyped-call]


def on_starting(server: "Arbiter") -> None:
    """Prepare multiprocessing directory for prometheus metrics collector."""
    prom_dir = pathlib.Path(
        os.environ.setdefault(
            "PROMETHEUS_MULTIPROC_DIR",
            os.path.join(gettempdir(), DEFAULT_PROMETHEUS_MULTIPROC_DIR_NAME),
        )
    )

    if prom_dir.exists():
        for p in prom_dir.rglob("*"):
            try:
                # Ensure that the cleanup doesn't silently fail on
                # files and subdirs created by other users.
                p.chmod(0o777)
            except Exception:
                pass

        shutil.rmtree(prom_dir, ignore_errors=True)

    prom_dir.mkdir(parents=True, exist_ok=True)

    # While `mkdir` sets mode=0o777 by default, this can be affected by umask resulting in
    # lesser permissions for other users. This step ensures the directory is writable for
    # all users.
    prom_dir.chmod(0o777)
