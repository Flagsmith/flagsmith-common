from datetime import time, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
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
