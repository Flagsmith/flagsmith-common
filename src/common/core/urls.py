from django.conf import settings
from django.urls import include, path, re_path

from common.core import views

urlpatterns = [
    path("version/", views.version_info),
    path("health/liveness/", views.liveness),
    path("health/readiness/", include("health_check.urls", namespace="health")),
    re_path(r"^health", include("health_check.urls", namespace="health-deprecated")),
    # Aptible health checks must be on /healthcheck and cannot redirect
    # see https://www.aptible.com/docs/core-concepts/apps/connecting-to-apps/app-endpoints/https-endpoints/health-checks
    re_path(r"^healthcheck", include("health_check.urls", namespace="health-aptible")),
]

if settings.PROMETHEUS_ENABLED:
    urlpatterns += [path("metrics/", views.metrics)]
