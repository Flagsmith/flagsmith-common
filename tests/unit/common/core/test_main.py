import os
from unittest.mock import patch

from common.core.main import ensure_cli_env


def test_ensure_cli_env__env_vars_set__calls_setup_logging_with_env_values() -> None:
    # Given
    env = {
        "LOG_LEVEL": "WARNING",
        "LOG_FORMAT": "json",
        "LOGGING_CONFIGURATION_FILE": "/tmp/logging.json",
        "APPLICATION_LOGGERS": "myapp,mylib",
    }

    # When
    with (
        patch.dict(os.environ, env, clear=False),
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
    )


def test_ensure_cli_env__no_env_vars__calls_setup_logging_with_defaults() -> None:
    # Given / When
    with (
        patch.dict(os.environ, {}, clear=False),
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
    )
