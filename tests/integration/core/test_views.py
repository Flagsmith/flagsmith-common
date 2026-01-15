import prometheus_client
import pytest
from pytest_mock import MockerFixture
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


def test_burn__default_duration__returns_expected(
    client: APIClient,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch("common.core.views.time.monotonic", side_effect=[0, 1])

    # When
    response = client.get("/burn/")

    # Then
    assert response.status_code == 200
    assert response.content.decode() == "waited"


def test_burn__custom_duration__returns_expected(
    client: APIClient,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch("common.core.views.time.monotonic", side_effect=[0, 3])

    # When
    response = client.get("/burn/?s=3")

    # Then
    assert response.status_code == 200
    assert response.content.decode() == "waited"
