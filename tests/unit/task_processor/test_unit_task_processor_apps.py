import typing

import pytest
from django.core.exceptions import ImproperlyConfigured
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from task_processor import apps


@pytest.mark.parametrize(
    "task_processor_databases",
    [
        # Default mode (try and consume remaining tasks from "default")
        ["default", "task_processor"],
        # Opt-out mode (try and consume remaining tasks from "task_processor")
        ["task_processor", "default"],
        # Single database mode
        ["task_processor"],
    ],
)
@pytest.mark.parametrize(
    "setup, expected_error",
    [
        (
            {  # Missing router and database
                "DATABASE_ROUTERS": [],
                "DATABASES": {"default": "exists but not task processor"},
            },
            "DATABASES must include 'task_processor' when using a separate task processor database.",
        ),
        (
            {  # Missing router
                "DATABASE_ROUTERS": [],
                "DATABASES": {
                    "default": "hooray",
                    "task_processor": "exists",
                },
            },
            "DATABASE_ROUTERS must include 'task_processor.routers.TaskProcessorRouter' when using a separate task processor database.",
        ),
        (
            {  # Missing database
                "DATABASE_ROUTERS": ["task_processor.routers.TaskProcessorRouter"],
                "DATABASES": {"default": "exists but not task processor"},
            },
            "DATABASES must include 'task_processor' when using a separate task processor database.",
        ),
    ],
)
def test_validates_django_settings_are_compatible_with_multi_database_setup(
    expected_error: str,
    mocker: MockerFixture,
    settings: SettingsWrapper,
    setup: dict[str, typing.Any],
    task_processor_databases: list[str],
) -> None:
    # Given
    settings.TASK_PROCESSOR_DATABASES = task_processor_databases
    settings.DATABASE_ROUTERS = setup["DATABASE_ROUTERS"]
    settings.DATABASES = setup["DATABASES"]
    task_processor_app = mocker.Mock()

    # When
    apps.TaskProcessorAppConfig.ready(task_processor_app)
    with pytest.raises(ImproperlyConfigured) as excinfo:
        apps.TaskProcessorAppConfig._validate_database_settings(task_processor_app)

    # Then
    task_processor_app._validate_database_settings.assert_called_once_with()
    assert str(excinfo.value) == expected_error
