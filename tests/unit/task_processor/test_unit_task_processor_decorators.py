import json
import logging
import typing
from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from pytest_django import DjangoCaptureOnCommitCallbacks
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from common.test_tools import AssertMetricFixture
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)
from task_processor.exceptions import InvalidArgumentsError, TaskProcessingError
from task_processor.models import RecurringTask, Task, TaskPriority
from task_processor.task_registry import get_task, initialise
from task_processor.task_run_method import TaskRunMethod


@pytest.fixture
def mock_thread_class(
    mocker: MockerFixture,
) -> MagicMock:
    mock_thread_class = mocker.patch(
        "task_processor.decorators.Thread",
        return_value=mocker.MagicMock(),
    )
    return mock_thread_class


@pytest.mark.django_db
def test_register_task_handler_run_in_thread__transaction_commit__true__default(
    caplog: pytest.LogCaptureFixture,
    mock_thread_class: MagicMock,
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    # Given
    caplog.set_level(logging.DEBUG)

    @register_task_handler()
    def my_function(*args: str, **kwargs: str) -> None:
        pass

    mock_thread = mock_thread_class.return_value

    args = ("foo",)
    kwargs = {"bar": "baz"}

    # When
    with django_capture_on_commit_callbacks(execute=True):
        my_function.run_in_thread(args=args, kwargs=kwargs)

    # Then
    mock_thread_class.assert_called_once_with(
        target=my_function.unwrapped, args=args, kwargs=kwargs, daemon=True
    )
    mock_thread.start.assert_called_once()

    assert len(caplog.records) == 1
    assert (
        caplog.records[0].message == "Running function my_function in unmanaged thread."
    )


def test_register_task_handler_run_in_thread__transaction_commit__false(
    caplog: pytest.LogCaptureFixture,
    mock_thread_class: MagicMock,
) -> None:
    # Given
    caplog.set_level(logging.DEBUG)

    @register_task_handler(transaction_on_commit=False)
    def my_function(*args: typing.Any, **kwargs: typing.Any) -> None:
        pass

    mock_thread = mock_thread_class.return_value

    args = ("foo",)
    kwargs = {"bar": "baz"}

    # When
    my_function.run_in_thread(args=args, kwargs=kwargs)

    # Then
    mock_thread_class.assert_called_once_with(
        target=my_function.unwrapped, args=args, kwargs=kwargs, daemon=True
    )
    mock_thread.start.assert_called_once()

    assert len(caplog.records) == 1
    assert (
        caplog.records[0].message == "Running function my_function in unmanaged thread."
    )


@pytest.mark.django_db
@pytest.mark.task_processor_mode
def test_register_recurring_task(
    mocker: MockerFixture,
) -> None:
    # Given
    mock = mocker.Mock()
    mock.__name__ = "a_function"
    task_kwargs = {"first_arg": "foo", "second_arg": "bar"}
    run_every = timedelta(minutes=10)
    task_identifier = "mock.a_function"

    # When
    register_recurring_task(
        run_every=run_every,
        kwargs=task_kwargs,
    )(mock)

    # Then
    initialise()

    task = RecurringTask.objects.get(task_identifier=task_identifier)
    assert task.serialized_kwargs == json.dumps(task_kwargs)
    assert task.run_every == run_every

    assert get_task(task_identifier)
    assert task.callable is mock


@pytest.mark.django_db
def test_register_recurring_task_does_nothing_if_not_run_by_processor() -> None:
    # Given

    task_kwargs = {"first_arg": "foo", "second_arg": "bar"}
    run_every = timedelta(minutes=10)
    task_identifier = "test_unit_task_processor_decorators.some_function"

    # When
    @register_recurring_task(
        run_every=run_every,
        kwargs=task_kwargs,
    )
    def some_function(first_arg: str, second_arg: str) -> None:
        pass

    # Then
    assert not RecurringTask.objects.filter(task_identifier=task_identifier).exists()
    with pytest.raises(TaskProcessingError):
        assert get_task(task_identifier)


def test_register_task_handler_validates_inputs() -> None:
    # Given
    @register_task_handler()
    def my_function(*args: typing.Any, **kwargs: typing.Any) -> None:
        pass

    class NonSerializableObj:
        pass

    # When
    with pytest.raises(InvalidArgumentsError):
        my_function(NonSerializableObj())


@pytest.mark.parametrize(
    "task_run_method", (TaskRunMethod.SEPARATE_THREAD, TaskRunMethod.SYNCHRONOUSLY)
)
def test_inputs_are_validated_when_run_without_task_processor(
    settings: SettingsWrapper, task_run_method: TaskRunMethod
) -> None:
    # Given
    settings.TASK_RUN_METHOD = task_run_method

    @register_task_handler()
    def my_function(*args: typing.Any, **kwargs: typing.Any) -> None:
        pass

    class NonSerializableObj:
        pass

    # When
    with pytest.raises(InvalidArgumentsError):
        my_function.delay(args=(NonSerializableObj(),))


@pytest.mark.django_db
def test_delay_returns_none_if_task_queue_is_full(settings: SettingsWrapper) -> None:
    # Given
    settings.TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR

    @register_task_handler(queue_size=1)
    def my_function(*args: typing.Any, **kwargs: typing.Any) -> None:
        pass

    for _ in range(10):
        Task.objects.create(
            task_identifier="test_unit_task_processor_decorators.my_function"
        )

    # When
    task = my_function.delay()

    # Then
    assert task is None


@pytest.mark.django_db
def test_delay__expected_metrics(
    settings: SettingsWrapper,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given
    settings.TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR

    @register_task_handler(queue_size=1)
    def my_function(*args: typing.Any, **kwargs: typing.Any) -> None:
        pass

    # When
    my_function.delay()

    # Then
    assert_metric(
        name="flagsmith_task_processor_enqueued_tasks_total",
        value=1.0,
        labels={"task_identifier": "test_unit_task_processor_decorators.my_function"},
    )


@pytest.mark.django_db
def test_can_create_task_with_priority(settings: SettingsWrapper) -> None:
    # Given
    settings.TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR

    @register_task_handler(priority=TaskPriority.HIGH)
    def my_function(*args: typing.Any, **kwargs: typing.Any) -> None:
        pass

    for _ in range(10):
        Task.objects.create(
            task_identifier="test_unit_task_processor_decorators.my_function"
        )

    # When
    task = my_function.delay()

    # Then
    assert task
    assert task.priority == TaskPriority.HIGH
