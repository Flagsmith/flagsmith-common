import prometheus_client
from django.conf import settings

http_requests_total = prometheus_client.Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["path", "method", "response_status"],
)
http_request_duration_seconds = prometheus_client.Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["path", "method", "response_status"],
    buckets=settings.PROMETHEUS_HISTOGRAM_BUCKETS,
)
