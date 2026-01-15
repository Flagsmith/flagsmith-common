from typing import Generator

import pytest


@pytest.fixture(autouse=True)
def reset_metrics_server_state() -> Generator[None, None, None]:
    """Reset the metrics server global state between tests."""
    from common.gunicorn import metrics_server

    metrics_server._server_started = False

    yield

    metrics_server._server_started = False
