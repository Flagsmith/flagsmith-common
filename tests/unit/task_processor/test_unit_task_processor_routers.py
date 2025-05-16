from itertools import combinations

import pytest
from django.apps import apps
from django.conf import settings
from django.db.models import Model
from pytest_mock import MockerFixture

from task_processor import routers


@pytest.mark.parametrize("model", apps.get_app_config("task_processor").get_models())
def test_TaskProcessorRouter__enabled__routes_queries_to_task_processor_database(
    mocker: MockerFixture,
    model: type[Model],
) -> None:
    # Given
    router = routers.TaskProcessorRouter()

    # When
    read_database = router.db_for_read(model)
    write_database = router.db_for_write(model)

    # Then
    assert read_database == write_database == "task_processor"


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
    router = routers.TaskProcessorRouter()

    # When
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
    router = routers.TaskProcessorRouter()

    # When
    allow_migrate = router.allow_migrate(database, app_label)

    # Then
    assert allow_migrate is expected
