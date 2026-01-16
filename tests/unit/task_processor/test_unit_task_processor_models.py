from datetime import time, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from freezegun import freeze_time
from pytest_mock import MockerFixture

from task_processor.decorators import register_task_handler
from task_processor.models import RecurringTask, Task
from task_processor.task_registry import initialise

now = timezone.now()
one_hour_ago = now - timedelta(hours=1)
one_hour_from_now = now + timedelta(hours=1)


def test_task_run(mocker: MockerFixture) -> None:
    # Given
    mock = mocker.Mock()
    mock.__name__ = "test_task"

    task_handler = register_task_handler()(mock)

    args = ("foo",)
    kwargs = {"arg_two": "bar"}

    initialise()

    task = Task.create(
        task_handler.task_identifier,
        scheduled_for=timezone.now(),
        args=args,
        kwargs=kwargs,
    )

    # When
    task.run()

    # Then
    mock.assert_called_once_with(*args, **kwargs)


def test_task_args__no_data__return_expected() -> None:
    # Given
    task = Task(
        task_identifier="test_task",
        scheduled_for=timezone.now(),
    )

    # When & Then
    assert task.args == ()


@pytest.mark.parametrize(
    "input, expected_output",
    (
        ({"value": Decimal("10")}, '{"value": 10}'),
        ({"value": Decimal("10.12345")}, '{"value": 10.12345}'),
    ),
)
def test_serialize_data_handles_decimal_objects(
    input: dict[str, Decimal],
    expected_output: str,
) -> None:
    assert Task.serialize_data(input) == expected_output


@pytest.mark.parametrize(
    "first_run_time, expected",
    ((one_hour_ago.time(), True), (one_hour_from_now.time(), False)),
)
def test_recurring_task_run_should_execute_first_run_at(
    first_run_time: time,
    expected: bool,
) -> None:
    assert (
        RecurringTask(
            first_run_time=first_run_time,
            run_every=timedelta(days=1),
        ).should_execute
        == expected
    )


@freeze_time("2026-01-15 23:05:23")
def test_recurring_task_should_execute__first_run_time_after_midnight__returns_false() -> (
    None
):
    # Given
    task = RecurringTask(
        first_run_time=time(0, 5, 23),
        run_every=timedelta(days=1),
    )

    # When & Then
    assert task.should_execute is False


@freeze_time("2026-01-16 00:30:00")
def test_recurring_task_should_execute__first_run_time_before_midnight__returns_true() -> (
    None
):
    # Given
    task = RecurringTask(
        first_run_time=time(23, 0, 0),
        run_every=timedelta(days=1),
    )

    # When & Then
    assert task.should_execute is True
