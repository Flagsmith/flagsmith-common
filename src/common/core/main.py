import contextlib
import logging
import os
import sys
import typing
from tempfile import mkdtemp

from django.core.management import (
    execute_from_command_line as django_execute_from_command_line,
)
from environs import Env

from common.core.cli import healthcheck
from common.core.logging import setup_logging
from common.gunicorn.processors import make_gunicorn_access_processor

env = Env()

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

    # Set up OTel instrumentation (opt-in via OTEL_EXPORTER_OTLP_ENDPOINT).
    otel_processors = None
    otel_endpoint = env.str("OTEL_EXPORTER_OTLP_ENDPOINT", None)
    if otel_endpoint:
        from common.core.otel import (
            add_otel_trace_context,
            build_otel_log_provider,
            build_tracer_provider,
            make_structlog_otel_processor,
            setup_tracing,
        )

        service_name = env.str("OTEL_SERVICE_NAME", "flagsmith-api")
        log_provider = build_otel_log_provider(
            endpoint=f"{otel_endpoint}/v1/logs",
            service_name=service_name,
        )
        otel_processors = [
            add_otel_trace_context,
            make_structlog_otel_processor(log_provider),
        ]
        tracer_provider = build_tracer_provider(
            endpoint=f"{otel_endpoint}/v1/traces",
            service_name=service_name,
        )
        excluded_urls = env.str("OTEL_TRACING_EXCLUDED_URL_PATHS", None)
        ctx.enter_context(setup_tracing(tracer_provider, excluded_urls=excluded_urls))
        ctx.callback(log_provider.shutdown)

    # Set up logging early, before Django settings are loaded.
    setup_logging(
        log_level=env.str("LOG_LEVEL", "INFO"),
        log_format=env.str("LOG_FORMAT", "generic"),
        logging_configuration_file=env.str("LOGGING_CONFIGURATION_FILE", None),
        application_loggers=env.list("APPLICATION_LOGGERS", []) or None,
        extra_foreign_processors=[
            make_gunicorn_access_processor(
                env.list("ACCESS_LOG_EXTRA_ITEMS", []) or None,
            ),
        ],
        otel_processors=otel_processors,
    )

    # Prometheus multiproc support
    if not os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = mkdtemp(prefix="flagsmith-prometheus-")

    # Currently we don't install Flagsmith modules as a package, so we need to add
    # $CWD to the Python path to be able to import them
    sys.path.append(os.getcwd())

    # TODO @khvn26 We should find a better way to pre-set the Django settings module
    # without resorting to it being set outside of the application
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.dev")

    if "docgen" in sys.argv:
        os.environ["DOCGEN_MODE"] = "true"

    if "task-processor" in sys.argv:
        # A hacky way to signal we're not running the API
        os.environ["RUN_BY_PROCESSOR"] = "true"

    with ctx:
        yield


def execute_from_command_line(argv: list[str]) -> None:
    try:
        subcommand = argv[1]
        subcommand_main = {
            "healthcheck": healthcheck.main,
            # Backwards compatibility for task-processor health checks
            # See https://github.com/Flagsmith/flagsmith-task-processor/issues/24
            "checktaskprocessorthreadhealth": healthcheck.main,
        }[subcommand]
    except (IndexError, KeyError):
        logger.info("Invoking Django")
    else:
        return subcommand_main(
            argv[2:],
            prog=f"{os.path.basename(argv[0])} {subcommand}",
        )
    django_execute_from_command_line(argv)


def main(argv: list[str] = sys.argv) -> None:
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
        # Run own commands and Django
        execute_from_command_line(argv)
