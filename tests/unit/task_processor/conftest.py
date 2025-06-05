import typing

import pytest
from pytest_django.fixtures import SettingsWrapper

from task_processor.task_registry import RegisteredTask


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    # Parametrize marked tests to run against both databases
    if marker := metafunc.definition.get_closest_marker("multi_database"):
        metafunc.parametrize(
            "current_database",
            [
                pytest.param(
                    database,
                    marks=pytest.mark.django_db(databases=[database], **marker.kwargs),
                )
                for database in ["default", "task_processor"]
            ],
            indirect=True,
        )


@pytest.fixture
def current_database(
    request: pytest.FixtureRequest,
    settings: SettingsWrapper,
) -> str:
    database: str = request.param
    settings.TASK_PROCESSOR_DATABASES = [database]
    if database == "task_processor":
        settings.DATABASE_ROUTERS = ["task_processor.routers.TaskProcessorRouter"]
    return database


@pytest.fixture(autouse=True)
def task_registry() -> typing.Generator[dict[str, RegisteredTask], None, None]:
    from task_processor.task_registry import registered_tasks

    registered_tasks.clear()
    yield registered_tasks
