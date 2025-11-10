import os
import pathlib
import shutil
from tempfile import gettempdir

from common.core.constants import DEFAULT_PROMETHEUS_MULTIPROC_DIR_NAME


def prepare_prom_multiproc_dir() -> None:
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
            except Exception:  # pragma: no cover
                pass

        shutil.rmtree(prom_dir, ignore_errors=True)

    prom_dir.mkdir(parents=True, exist_ok=True)

    # While `mkdir` sets mode=0o777 by default, this can be affected by umask resulting in
    # lesser permissions for other users. This step ensures the directory is writable for
    # all users.
    prom_dir.chmod(0o777)
