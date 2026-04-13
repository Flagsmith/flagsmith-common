import os

import pytest
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk.trace import TracerProvider
from pytest_mock import MockerFixture
from structlog.typing import Processor

from common.core.main import ensure_cli_env
from common.core.otel import add_otel_trace_context


def test_ensure_cli_env__env_vars_set__calls_setup_logging_with_env_values(
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
) -> None:
    # Given
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("LOG_FORMAT", "json")
    monkeypatch.setenv("LOGGING_CONFIGURATION_FILE", "/tmp/logging.json")
    monkeypatch.setenv("APPLICATION_LOGGERS", "myapp,mylib")
    monkeypatch.setenv("ACCESS_LOG_EXTRA_ITEMS", "{flagsmith.route}e,{origin}i")

    mock_setup = mocker.patch("common.core.main.setup_logging")

    # When
    with ensure_cli_env():
        pass

    # Then
    mock_setup.assert_called_once_with(
        log_level="WARNING",
        log_format="json",
        logging_configuration_file="/tmp/logging.json",
        application_loggers=["myapp", "mylib"],
        extra_foreign_processors=mocker.ANY,
        otel_processors=None,
    )


def test_ensure_cli_env__no_env_vars__calls_setup_logging_with_defaults(
    mocker: MockerFixture,
) -> None:
    # Given / When
    mock_setup = mocker.patch("common.core.main.setup_logging")

    with ensure_cli_env():
        pass

    # Then
    mock_setup.assert_called_once_with(
        log_level="INFO",
        log_format="generic",
        logging_configuration_file=None,
        application_loggers=None,
        extra_foreign_processors=mocker.ANY,
        otel_processors=None,
    )


def test_ensure_cli_env__otel_endpoint_set__configures_otel_processors(
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
) -> None:
    # Given
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")

    mock_log_provider = mocker.MagicMock(spec=LoggerProvider)
    mock_tracer_provider = mocker.MagicMock(spec=TracerProvider)
    mock_otel_log_processor = mocker.MagicMock(spec=Processor)

    mock_setup = mocker.patch("common.core.main.setup_logging")
    mock_build_log = mocker.patch(
        "common.core.otel.build_otel_log_provider",
        return_value=mock_log_provider,
    )
    mock_build_tracer = mocker.patch(
        "common.core.otel.build_tracer_provider",
        return_value=mock_tracer_provider,
    )
    mock_make_processor = mocker.patch(
        "common.core.otel.make_structlog_otel_processor",
        return_value=mock_otel_log_processor,
    )
    mock_setup_tracing = mocker.patch("common.core.otel.setup_tracing")

    # When
    with ensure_cli_env():
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


def test_ensure_cli_env__otel_custom_service_name_and_excluded_urls__passes_to_providers(
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
) -> None:
    # Given
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "my-service")
    monkeypatch.setenv(
        "OTEL_TRACING_EXCLUDED_URL_PATHS", "health/liveness,health/readiness"
    )

    mock_build_log = mocker.patch(
        "common.core.otel.build_otel_log_provider",
        return_value=mocker.MagicMock(spec=LoggerProvider),
    )
    mock_build_tracer = mocker.patch(
        "common.core.otel.build_tracer_provider",
        return_value=mocker.MagicMock(spec=TracerProvider),
    )
    mock_setup_tracing = mocker.patch("common.core.otel.setup_tracing")

    # When
    with ensure_cli_env():
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


def test_ensure_cli_env__docgen_in_argv__sets_docgen_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setattr("sys.argv", ["flagsmith", "docgen", "metrics"])

    # When / Then
    with ensure_cli_env():
        assert os.environ.get("DOCGEN_MODE") == "true"


def test_ensure_cli_env__task_processor_in_argv__sets_run_by_processor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setattr("sys.argv", ["flagsmith", "task-processor"])

    # When / Then
    with ensure_cli_env():
        assert os.environ.get("RUN_BY_PROCESSOR") == "true"


@pytest.mark.parametrize(
    "argv,expected_otel_service_name",
    [
        pytest.param(
            ["flagsmith", "task-processor"],
            "flagsmith-task-processor",
            id="task_processor",
        ),
        pytest.param(
            ["flagsmith", "anything-else"],
            "flagsmith-api",
            id="anything_else",
        ),
    ],
)
def test_ensure_cli_env__argv__expected_otel_service_name(
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
    argv: list[str],
    expected_otel_service_name: str,
) -> None:
    # Given
    monkeypatch.setattr("sys.argv", argv)
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")

    mock_build_log = mocker.patch(
        "common.core.otel.build_otel_log_provider",
        return_value=mocker.MagicMock(spec=LoggerProvider),
    )
    mock_build_tracer = mocker.patch(
        "common.core.otel.build_tracer_provider",
        return_value=mocker.MagicMock(spec=TracerProvider),
    )
    mocker.patch("common.core.otel.setup_tracing")

    # When
    with ensure_cli_env():
        pass

    # Then
    mock_build_log.assert_called_once_with(
        endpoint="http://collector:4318/v1/logs",
        service_name=expected_otel_service_name,
    )
    mock_build_tracer.assert_called_once_with(
        endpoint="http://collector:4318/v1/traces",
        service_name=expected_otel_service_name,
    )


def test_ensure_cli_env__env_service_name__expected_otel_service_name(
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
) -> None:
    # Given
    monkeypatch.setattr("sys.argv", ["flagsmith", "task-processor"])
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "my-custom")

    mock_build_log = mocker.patch(
        "common.core.otel.build_otel_log_provider",
        return_value=mocker.MagicMock(spec=LoggerProvider),
    )
    mock_build_tracer = mocker.patch(
        "common.core.otel.build_tracer_provider",
        return_value=mocker.MagicMock(spec=TracerProvider),
    )
    mocker.patch("common.core.otel.setup_tracing")

    # When
    with ensure_cli_env():
        pass

    # Then
    mock_build_log.assert_called_once_with(
        endpoint="http://collector:4318/v1/logs",
        service_name="my-custom",
    )
    mock_build_tracer.assert_called_once_with(
        endpoint="http://collector:4318/v1/traces",
        service_name="my-custom",
    )
