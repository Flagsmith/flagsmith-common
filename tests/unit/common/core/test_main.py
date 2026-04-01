import os
from unittest.mock import ANY, MagicMock, patch

from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk.trace import TracerProvider
from structlog.typing import Processor

from common.core.main import ensure_cli_env
from common.core.otel import add_otel_trace_context


def test_ensure_cli_env__env_vars_set__calls_setup_logging_with_env_values() -> None:
    # Given
    env = {
        "LOG_LEVEL": "WARNING",
        "LOG_FORMAT": "json",
        "LOGGING_CONFIGURATION_FILE": "/tmp/logging.json",
        "APPLICATION_LOGGERS": "myapp,mylib",
        "ACCESS_LOG_EXTRA_ITEMS": "{flagsmith.route}e,{origin}i",
    }

    # When
    with (
        patch.dict(os.environ, env),
        patch("common.core.main.setup_logging") as mock_setup,
        ensure_cli_env(),
    ):
        pass

    # Then
    mock_setup.assert_called_once_with(
        log_level="WARNING",
        log_format="json",
        logging_configuration_file="/tmp/logging.json",
        application_loggers=["myapp", "mylib"],
        extra_foreign_processors=ANY,
        otel_processors=None,
    )


def test_ensure_cli_env__no_env_vars__calls_setup_logging_with_defaults() -> None:
    # Given / When
    with (
        patch.dict(os.environ, {}),
        patch("common.core.main.setup_logging") as mock_setup,
        ensure_cli_env(),
    ):
        pass

    # Then
    mock_setup.assert_called_once_with(
        log_level="INFO",
        log_format="generic",
        logging_configuration_file=None,
        application_loggers=None,
        extra_foreign_processors=ANY,
        otel_processors=None,
    )


def test_ensure_cli_env__otel_endpoint_set__configures_otel_processors() -> None:
    # Given
    env = {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://collector:4318"}
    mock_log_provider = MagicMock(spec=LoggerProvider)
    mock_tracer_provider = MagicMock(spec=TracerProvider)
    mock_otel_log_processor = MagicMock(spec=Processor)

    # When
    with (
        patch.dict(os.environ, env),
        patch("common.core.main.setup_logging") as mock_setup,
        patch(
            "common.core.otel.build_otel_log_provider",
            return_value=mock_log_provider,
        ) as mock_build_log,
        patch(
            "common.core.otel.build_tracer_provider",
            return_value=mock_tracer_provider,
        ) as mock_build_tracer,
        patch(
            "common.core.otel.make_structlog_otel_processor",
            return_value=mock_otel_log_processor,
        ) as mock_make_processor,
        patch("common.core.otel.setup_tracing") as mock_setup_tracing,
        ensure_cli_env(),
    ):
        pass

    # Then — OTel providers are built with the right endpoint and service name
    mock_build_log.assert_called_once_with(
        endpoint="http://collector:4318/v1/logs",
        service_name="flagsmith-api",
    )
    mock_make_processor.assert_called_once_with(mock_log_provider)
    mock_build_tracer.assert_called_once_with(
        endpoint="http://collector:4318/v1/traces",
        service_name="flagsmith-api",
    )
    mock_setup_tracing.assert_called_once_with(mock_tracer_provider, excluded_urls=None)

    # setup_logging receives the exact OTel processors list
    call_kwargs = mock_setup.call_args.kwargs
    assert call_kwargs["otel_processors"] == [
        add_otel_trace_context,
        mock_otel_log_processor,
    ]


def test_ensure_cli_env__otel_custom_service_name_and_excluded_urls__passes_to_providers() -> (
    None
):
    # Given
    env = {
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://collector:4318",
        "OTEL_SERVICE_NAME": "my-service",
        "OTEL_TRACING_EXCLUDED_URL_PATHS": "health/liveness,health/readiness",
    }

    # When
    with (
        patch.dict(os.environ, env),
        patch("common.core.main.setup_logging"),
        patch(
            "common.core.otel.build_otel_log_provider",
            return_value=MagicMock(spec=LoggerProvider),
        ) as mock_build_log,
        patch(
            "common.core.otel.build_tracer_provider",
            return_value=MagicMock(spec=TracerProvider),
        ) as mock_build_tracer,
        patch("common.core.otel.setup_tracing") as mock_setup_tracing,
        ensure_cli_env(),
    ):
        pass

    # Then
    mock_build_log.assert_called_once_with(
        endpoint="http://collector:4318/v1/logs",
        service_name="my-service",
    )
    mock_build_tracer.assert_called_once_with(
        endpoint="http://collector:4318/v1/traces",
        service_name="my-service",
    )
    mock_setup_tracing.assert_called_once_with(
        mock_build_tracer.return_value,
        excluded_urls="health/liveness,health/readiness",
    )
