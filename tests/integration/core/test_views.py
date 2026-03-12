import prometheus_client
import pytest
from rest_framework.test import APIClient

from common.test_tools import SnapshotFixture


def test_liveness_probe__default_request__returns_expected(
    client: APIClient,
) -> None:
    # Given
    url = "/health/liveness/"

    # When
    response = client.get(url)

    # Then
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.prometheus_multiprocess_mode
def test_metrics__default_request__returns_expected(
    test_metric: prometheus_client.Counter,
    client: APIClient,
    snapshot: SnapshotFixture,
) -> None:
    # Given
    test_metric.labels(
        test_name="test_metrics__default_request__returns_expected"
    ).inc()

    # When
    response = client.get("/metrics", follow=True)

    # Then
    assert response.status_code == 200
    assert response.content.decode() == snapshot()
