import typing

import pytest
from django.core.exceptions import ImproperlyConfigured
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from task_processor import apps
from task_processor.health import TaskProcessorHealthCheckBackend
from task_processor.task_run_method import TaskRunMethod


def test_skips_validation_if_task_run_method_is_not_task_processor(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.TASK_RUN_METHOD = TaskRunMethod.SYNCHRONOUSLY
    task_processor_app = mocker.Mock()

    # When
    apps.TaskProcessorAppConfig.ready(task_processor_app)

    # Then
    task_processor_app._validate_database_settings.assert_not_called()
    task_processor_app._register_health_check.assert_not_called()


@pytest.mark.parametrize(
    "enabled, expected_call",
    [
        (True, ((TaskProcessorHealthCheckBackend,), {})),
        (False, None),
    ],
)
def test_registers_health_check_if_enabled(
    enabled: bool,
    mocker: MockerFixture,
    expected_call: tuple[typing.Any, ...],
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR
    settings.ENABLE_TASK_PROCESSOR_HEALTH_CHECK = enabled
    plugin_dir = mocker.patch.object(apps, "plugin_dir")
    task_processor_app = mocker.Mock()

    # When
    apps.TaskProcessorAppConfig.ready(task_processor_app)
    apps.TaskProcessorAppConfig._register_health_check(task_processor_app)

    # Then
    task_processor_app._register_health_check.assert_called_once_with()
    assert plugin_dir.register.call_args == expected_call


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
