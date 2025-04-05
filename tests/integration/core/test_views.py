import prometheus_client
from rest_framework.test import APIClient


def test_liveness_probe__return_expected(
    client: APIClient,
) -> None:
    response = client.get("/health/liveness/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics__return_expected(
    test_metric: prometheus_client.Counter,
    client: APIClient,
) -> None:
    # Arrange
    test_metric.labels(test_name="test_metrics__return_expected").inc()

    # Act
    response = client.get("/metrics", follow=True)

    # Assert
    assert response.status_code == 200
    assert response.content == (
        "\n".join(
            [
                "# HELP pytest_tests_run_total Total number of tests run by pytest",
                "# TYPE pytest_tests_run_total counter",
                'pytest_tests_run_total{test_name="test_metrics__return_expected"} 1.0',
                "",
            ]
        ).encode()
    )
