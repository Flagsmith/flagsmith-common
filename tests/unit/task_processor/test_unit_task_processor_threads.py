import logging
from typing import Type

import pytest
from django.db import DatabaseError
from pytest_mock import MockerFixture

from task_processor.threads import TaskRunner


@pytest.mark.parametrize(
    "exception_class, exception_message",
    [(DatabaseError, "Database error"), (Exception, "Generic error")],
)
@pytest.mark.django_db
def test_task_runner_is_resilient_to_errors(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    exception_class: Type[Exception],
    exception_message: str,
) -> None:
    # Given
    task_runner = TaskRunner()
    mocker.patch(
        "task_processor.threads.run_tasks",
        side_effect=exception_class(exception_message),
    )

    # When
    task_runner.run_iteration()

    # Then
    assert len(caplog.records) == 1

    assert caplog.records[0].levelno == logging.ERROR
    assert (
        caplog.records[0].message
        == f"Received error retrieving tasks: {exception_message}."
    )
