from datetime import datetime, timedelta

import prometheus_client
import pytest

from common.test_tools import AssertMetricFixture, RunTasksFixture
from common.test_tools.plugin import assert_metric_impl
from common.test_tools.utils import edition_printer
from task_processor.decorators import register_task_handler
from task_processor.models import Task


def test_assert_metrics__metric_incremented__asserts_expected(
    assert_metric: AssertMetricFixture,
    test_metric: prometheus_client.Counter,
) -> None:
    # Given
    test_metric.labels(test_name="test_assert_metrics__asserts_expected").inc()

    # When & Then
    assert_metric(
        name="pytest_tests_run_total",
        labels={"test_name": "test_assert_metrics__asserts_expected"},
        value=1,
    )


def test_assert_metrics__after_registry_reset__raises_assertion(
    test_metric: prometheus_client.Counter,
) -> None:
    # Given
    test_metric.labels(test_name="test_assert_metrics__registry_reset_expected").inc()

    assert_metric_gen = assert_metric_impl()
    assert_metric = next(assert_metric_gen)
    next(assert_metric_gen, None)

    # When & Then
    with pytest.raises(AssertionError):
        assert_metric(
            name="pytest_tests_run_total",
            labels={"test_name": "test_assert_metrics__registry_reset_expected"},
            value=1,
        )


def test_edition_printer__no_marker__returns_oss() -> None:
    # Given / When
    result = edition_printer()

    # Then
    assert result == "oss!"


@pytest.mark.saas_mode
def test_edition_printer__saas_mode__returns_saas() -> None:
    # Given / When
    result = edition_printer()

    # Then
    assert result == "saas!"


@pytest.mark.enterprise_mode
def test_edition_printer__enterprise_mode__returns_enterprise() -> None:
    # Given / When
    result = edition_printer()

    # Then
    assert result == "enterprise!"


def test_run_tasks__single_task_delayed__runs_expected(
    run_tasks: RunTasksFixture,
) -> None:
    # Given
    @register_task_handler()
    def my_task() -> None:
        return None

    my_task.delay()

    # When
    task_runs = run_tasks(num_tasks=1)

    # Then
    assert len(task_runs) == 1
    assert task_runs[0].task.task_identifier == "test_plugin.my_task"
    assert task_runs[0].result == "SUCCESS"


def test_run_tasks__delay_inside_task__runs_expected(
    run_tasks: RunTasksFixture,
) -> None:
    # Given
    @register_task_handler()
    def my_task() -> None: ...

    @register_task_handler()
    def calling_task() -> None:
        my_task.delay(delay_until=datetime.now() + timedelta(hours=1))

    calling_task.delay()

    # When
    task_runs = run_tasks(num_tasks=1)

    # Then
    assert len(task_runs) == 1
    assert Task.objects.count() == 2
    assert Task.objects.latest("scheduled_for").task_identifier == "test_plugin.my_task"
