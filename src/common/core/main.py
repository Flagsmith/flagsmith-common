import logging
import os
import sys
import tempfile

from django.core.management import execute_from_command_line

logger = logging.getLogger(__name__)


def ensure_cli_env() -> None:
    """
    Set up the environment for the main entry point of the application.
    """
    # TODO @khvn26 Move logging setup to here

    # Currently we don't install Flagsmith modues as a package, so we need to add
    # $CWD to the Python path to be able to import them
    sys.path.append(os.getcwd())

    # TODO @khvn26 We should find a better way to pre-set the Django settings module
    # without resorting to it being set outside of the application
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.dev")

    # Set up Prometheus' multiprocess mode
    if "PROMETHEUS_MULTIPROC_DIR" not in os.environ:
        prometheus_multiproc_dir = tempfile.TemporaryDirectory(
            prefix="prometheus_multiproc",
            delete=False,
        )
        logger.info(
            "Created %s for Prometheus multi-process mode",
            prometheus_multiproc_dir.name,
        )
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = prometheus_multiproc_dir.name


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
    ensure_cli_env()

    # Run Django
    execute_from_command_line(sys.argv)
