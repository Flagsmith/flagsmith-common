"""
Standalone Prometheus metrics HTTP server.

This module provides a separate HTTP server for Prometheus metrics,
independent of the main Gunicorn application server. This improves
metrics reliability under high API load.

The server runs in a daemon thread and serves metrics from the shared
PROMETHEUS_MULTIPROC_DIR directory.
"""

import logging
import os
import threading

from prometheus_client import CollectorRegistry, start_http_server
from prometheus_client.multiprocess import MultiProcessCollector

logger = logging.getLogger(__name__)

METRICS_SERVER_PORT = 9100

_server_started = False
_server_lock = threading.Lock()


def get_multiprocess_registry() -> CollectorRegistry:
    """Create a registry configured for multiprocess metric collection."""
    registry = CollectorRegistry()
    MultiProcessCollector(registry)  # type: ignore[no-untyped-call]
    return registry


def start_metrics_server(
    port: int = METRICS_SERVER_PORT,
) -> None:
    """
    Start the standalone Prometheus metrics HTTP server.

    This function is idempotent - calling it multiple times will only
    start one server. The server runs in a daemon thread.

    Args:
        port: The port to serve metrics on. Defaults to 9100.
    """
    global _server_started

    with _server_lock:
        if _server_started:
            logger.debug("Metrics server already started")
            return

        prometheus_multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
        if not prometheus_multiproc_dir:
            logger.warning("PROMETHEUS_MULTIPROC_DIR not set, skipping metrics server")
            return

        registry = get_multiprocess_registry()

        try:
            start_http_server(port=port, registry=registry)
            _server_started = True
            logger.info("Prometheus metrics server started on port %d", port)
        except OSError as e:
            logger.error("Failed to start metrics server on port %d: %s", port, e)
