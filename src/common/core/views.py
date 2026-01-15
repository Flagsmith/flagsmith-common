import logging
import time

import prometheus_client
from django.http import HttpResponse, JsonResponse
from rest_framework.request import Request

from common.core import utils
from common.prometheus.utils import get_registry

logger = logging.getLogger(__name__)


def liveness(request: Request) -> JsonResponse:
    return JsonResponse({"status": "ok"})


def version_info(request: Request) -> JsonResponse:
    return JsonResponse(utils.get_version_info())


def metrics(request: Request) -> HttpResponse:
    registry = get_registry()
    metrics_page = prometheus_client.generate_latest(registry)
    return HttpResponse(
        metrics_page,
        content_type=prometheus_client.CONTENT_TYPE_LATEST,
    )


def burn(request: Request) -> HttpResponse:
    """
    Burn CPU for a specified duration to simulate load.

    Usage: GET /burn?s=10 (burns CPU for 10 seconds)
    """
    seconds = int(request.GET.get("s", 1))
    end_time = time.monotonic() + seconds
    while time.monotonic() < end_time:
        pass  # Busy wait

    return HttpResponse("waited")
