import typing

import pytest
from pytest_django.fixtures import SettingsWrapper

from common.prometheus.utils import reload_metrics
from task_processor.task_registry import RegisteredTask


@pytest.fixture()
def task_processor_mode(settings: SettingsWrapper) -> None:
    settings.TASK_PROCESSOR_MODE = True
    # The setting is supposed to be set before the metrics module is imported,
    # so reload it
    reload_metrics("task_processor.metrics")


@pytest.fixture(autouse=True)
def task_processor_mode_marked(request: pytest.FixtureRequest) -> None:
    for marker in request.node.iter_markers():
        if marker.name == "task_processor_mode":
            request.getfixturevalue("task_processor_mode")
            return


@pytest.fixture(autouse=True)
def task_registry() -> typing.Generator[dict[str, RegisteredTask], None, None]:
    from task_processor.task_registry import registered_tasks

    registered_tasks.clear()
    yield registered_tasks
