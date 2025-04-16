import prometheus_client
import pytest

from common.test_tools import AssertMetricFixture
from common.test_tools.plugin import assert_metric_impl


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


@pytest.mark.saas_mode
def test_saas_mode_marker__is_saas_returns_expected() -> None:
    # Given
    from common.core.utils import is_saas

    # When & Then
    assert is_saas() is True


@pytest.mark.enterprise_mode
def test_enterprise_mode_marker__is_enterprise_returns_expected() -> None:
    # Given
    from common.core.utils import is_enterprise

    # When & Then
    assert is_enterprise() is True
