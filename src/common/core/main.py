import logging
import os
import sys
import tempfile

from django.core.management import execute_from_command_line

logger = logging.getLogger(__name__)


def main() -> None:
    """
    The main entry point to the Flagsmith application.

    An equivalent to Django's `manage.py` script, this module is used to run management commands.

    It's installed as the `flagsmith` command.

    Everything that needs to be run before Django is started should be done here.

    The end goal is to eventually replace Core API's `run-docker.sh` with this.

    Usage:
    `flagsmith <command> [options]`
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.dev")

    # Set up Prometheus' multiprocess mode
    if "PROMETHEUS_MULTIPROC_DIR" not in os.environ:
        prometheus_multiproc_dir = tempfile.TemporaryDirectory(
            prefix="prometheus_multiproc",
        )
        logger.info(
            "Created %s for Prometheus multi-process mode",
            prometheus_multiproc_dir.name,
        )
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = prometheus_multiproc_dir.name

    # Run Django
    execute_from_command_line(sys.argv)
