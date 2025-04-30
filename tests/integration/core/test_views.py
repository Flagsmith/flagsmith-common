import prometheus_client
import pytest
from rest_framework.test import APIClient

from common.test_tools import SnapshotFixture


def test_liveness_probe__return_expected(
    client: APIClient,
) -> None:
    response = client.get("/health/liveness/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.prometheus_multiprocess_mode
def test_metrics__return_expected(
    test_metric: prometheus_client.Counter,
    client: APIClient,
    snapshot: SnapshotFixture,
) -> None:
    # Arrange
    test_metric.labels(test_name="test_metrics__return_expected").inc()

    # Act
    response = client.get("/metrics", follow=True)

    # Assert
    assert response.status_code == 200
    assert response.content.decode() == snapshot()
