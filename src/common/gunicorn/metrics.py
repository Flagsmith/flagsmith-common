import prometheus_client

from common.gunicorn.constants import HTTP_SERVER_RESPONSE_SIZE_DEFAULT_BUCKETS
from common.prometheus import Histogram

flagsmith_http_server_requests_total = prometheus_client.Counter(
    "flagsmith_http_server_requests_total",
    "Total number of HTTP requests.",
    ["route", "method", "response_status"],
)
flagsmith_http_server_request_duration_seconds = Histogram(
    "flagsmith_http_server_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["route", "method", "response_status"],
)
flagsmith_http_server_response_size_bytes = Histogram(
    "flagsmith_http_server_response_size_bytes",
    "HTTP response size in bytes.",
    ["route", "method", "response_status"],
    buckets=HTTP_SERVER_RESPONSE_SIZE_DEFAULT_BUCKETS,
)
