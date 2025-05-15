from itertools import combinations

import pytest
from django.apps import apps
from django.conf import settings
from django.db.models import Model
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from task_processor import routers


@pytest.mark.parametrize(
    "given_settings, expected",
    [
        ({"TASK_PROCESSOR_DATABASES": ["task_processor"]}, True),
        ({"TASK_PROCESSOR_DATABASES": ["default", "task_processor"]}, True),
        ({"TASK_PROCESSOR_DATABASES": ["default"]}, False),
    ],
)
def test_TaskProcessorRouter__checks_whether_is_enabled(
    settings: SettingsWrapper,
    given_settings: dict[str, None | str],
    expected: bool,
) -> None:
    # Given
    for key, value in given_settings.items():
        setattr(settings, key, value)

    # When
    router = routers.TaskProcessorRouter()

    # Then
    assert router.is_enabled is expected


@pytest.mark.parametrize("model", apps.get_app_config("task_processor").get_models())
def test_TaskProcessorRouter__enabled__routes_queries_to_task_processor_database(
    mocker: MockerFixture,
    model: type[Model],
) -> None:
    # Given
    mocker.patch.object(routers.TaskProcessorRouter, "is_enabled", new=True)

    # When
    router = routers.TaskProcessorRouter()
    read_database = router.db_for_read(model)
    write_database = router.db_for_write(model)

    # Then
    assert read_database == write_database == "task_processor"


@pytest.mark.parametrize("model", apps.get_app_config("task_processor").get_models())
def test_TaskProcessorRouter__disabled__does_not_route_database_queries(
    mocker: MockerFixture,
    model: type[Model],
) -> None:
    # Given
    mocker.patch.object(routers.TaskProcessorRouter, "is_enabled", new=False)

    # When
    router = routers.TaskProcessorRouter()
    read_database = router.db_for_read(model)
    write_database = router.db_for_write(model)
    allows_relation = router.allow_relation(model(), model())
    allows_migrate = {
        router.allow_migrate("default", app_label="task_processor"),
        router.allow_migrate("task_processor", app_label="task_processor"),
        router.allow_migrate("other", app_label="task_processor"),
        router.allow_migrate("task_processor", app_label="other"),
    }

    # Then
    assert read_database is None
    assert write_database is None
    assert allows_relation is None
    assert allows_migrate == {None}


@pytest.mark.parametrize(
    "model1, model2, expected",
    [  # True if both models are from task_processor app
        (*model_pair, True)
        for model_pair in combinations(
            apps.get_app_config("task_processor").get_models(), 2
        )
    ]
    + [  # None if either model is not from task_processor app
        (model, apps.get_model(settings.AUTH_USER_MODEL), None)
        for model in apps.get_app_config("task_processor").get_models()
    ],
)
def test_TaskProcessorRouter__allow_relation__returns_according_to_given_models(
    mocker: MockerFixture,
    model1: type[Model],
    model2: type[Model],
    expected: bool,
) -> None:
    # Given
    mocker.patch.object(routers.TaskProcessorRouter, "is_enabled", new=True)

    # When
    router = routers.TaskProcessorRouter()
    allow_relation = router.allow_relation(model1(), model2())

    # Then
    assert allow_relation is expected


@pytest.mark.parametrize(
    "database, app_label, expected",
    [
        ("task_processor", "task_processor", True),
        ("default", "task_processor", True),
        ("other", "task_processor", False),
        ("task_processor", "other", None),
        ("default", "other", None),
        ("other", "other", None),
    ],
)
def test_TaskProcessorRouter__allow_migrate__applies_to_both_databases(
    app_label: str,
    database: str,
    expected: bool,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.object(routers.TaskProcessorRouter, "is_enabled", new=True)

    # When
    router = routers.TaskProcessorRouter()
    allow_migrate = router.allow_migrate(database, app_label)

    # Then
    assert allow_migrate is expected
