import prometheus_client
import pytest

from common.test_tools import AssertMetricFixture, RunTasksFixture
from common.test_tools.plugin import assert_metric_impl
from common.test_tools.utils import edition_printer
from task_processor.decorators import register_task_handler


def test_assert_metrics__asserts_expected(
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


def test_assert_metrics__registry_reset_expected(
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


def test_no_marker__oss_edition_expected() -> None:
    # When & Then
    assert edition_printer() == "oss!"


@pytest.mark.saas_mode
def test_saas_mode_marker__is_saas_returns_expected() -> None:
    # When & Then
    assert edition_printer() == "saas!"


@pytest.mark.enterprise_mode
def test_enterprise_mode_marker__is_enterprise_returns_expected() -> None:
    # When & Then
    assert edition_printer() == "enterprise!"


def test_run_tasks__runs_expected_tasks(
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
