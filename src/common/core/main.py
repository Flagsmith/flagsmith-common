import contextlib
import logging
import os
import sys
import tempfile
import typing

from django.core.management import execute_from_command_line

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def ensure_cli_env() -> typing.Generator[None, None, None]:
    """
    Set up the environment for the main entry point of the application
    and clean up after it's done.

    Add environment-related code that needs to happen before and after Django is involved
    to here.

    Use as a context manager, e.g.:

    ```python
    with ensure_cli_env():
        main()
    ```
    """
    ctx = contextlib.ExitStack()

    # TODO @khvn26 Move logging setup to here

    # Currently we don't install Flagsmith modules as a package, so we need to add
    # $CWD to the Python path to be able to import them
    sys.path.append(os.getcwd())

    # TODO @khvn26 We should find a better way to pre-set the Django settings module
    # without resorting to it being set outside of the application
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.dev")

    # Set up Prometheus' multiprocess mode
    if "PROMETHEUS_MULTIPROC_DIR" not in os.environ:
        prometheus_multiproc_dir_name = tempfile.mkdtemp()

        logger.info(
            "Created %s for Prometheus multi-process mode",
            prometheus_multiproc_dir_name,
        )
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = prometheus_multiproc_dir_name

    if "task-processor" in sys.argv:
        # A hacky way to signal we're not running the API
        os.environ["RUN_BY_PROCESSOR"] = "true"

    with ctx:
        yield


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
    with ensure_cli_env():
        # Run Django
        execute_from_command_line(sys.argv)
