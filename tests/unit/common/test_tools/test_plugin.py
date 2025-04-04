import prometheus_client
import pytest

from common.test_tools import AssertMetricFixture
from common.test_tools.plugin import assert_metric_impl

test_metric = prometheus_client.Counter(
    "pytest_tests_run_total",
    "Total number of tests run by pytest",
    ["test_name"],
)


def test_assert_metrics__asserts_expected(
    assert_metric: AssertMetricFixture,
) -> None:
    # Given
    test_metric.labels(test_name="test_assert_metrics__asserts_expected").inc()

    # When & Then
    assert_metric(
        name="pytest_tests_run_total",
        labels={"test_name": "test_assert_metrics__asserts_expected"},
        value=1,
    )


def test_assert_metrics__registry_reset_expected() -> None:
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
