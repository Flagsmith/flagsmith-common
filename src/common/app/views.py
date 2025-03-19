import logging

from django.http import JsonResponse
from rest_framework.request import Request

from common.app import utils

logger = logging.getLogger(__name__)


def version_info(request: Request) -> JsonResponse:
    return JsonResponse(utils.get_version_info())
