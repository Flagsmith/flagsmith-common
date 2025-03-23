import os
import sys

from django.core.management import execute_from_command_line


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
    os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp")

    # Run Django
    execute_from_command_line(sys.argv)
