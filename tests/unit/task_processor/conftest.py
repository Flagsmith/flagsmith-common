import logging
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


class GetTaskProcessorCaplog(typing.Protocol):
    def __call__(
        self, log_level: str | int = logging.INFO
    ) -> pytest.LogCaptureFixture: ...


@pytest.fixture
def get_task_processor_caplog(
    caplog: pytest.LogCaptureFixture,
) -> GetTaskProcessorCaplog:
    # caplog doesn't allow you to capture logging outputs from loggers that don't
    # propagate to root. Quick hack here to get the task_processor logger to
    # propagate.
    # TODO: look into using loguru.

    def _inner(log_level: str | int = logging.INFO) -> pytest.LogCaptureFixture:
        task_processor_logger = logging.getLogger("task_processor")
        task_processor_logger.propagate = True
        # Assume required level for the logger.
        task_processor_logger.setLevel(log_level)
        caplog.set_level(log_level)
        return caplog

    return _inner


@pytest.fixture(autouse=True)
def task_registry() -> typing.Generator[dict[str, RegisteredTask], None, None]:
    from task_processor.task_registry import registered_tasks

    registered_tasks.clear()
    yield registered_tasks
