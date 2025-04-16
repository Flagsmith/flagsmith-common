import prometheus_client
import pytest

from common.test_tools import AssertMetricFixture
from common.test_tools.plugin import assert_metric_impl
from common.test_tools.utils import edition_printer


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
