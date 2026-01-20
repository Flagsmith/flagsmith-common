import logging

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
