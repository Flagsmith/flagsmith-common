import prometheus_client

from common.prometheus import Histogram

flagsmith_http_server_requests_total = prometheus_client.Counter(
    "flagsmith_http_server_requests_total",
    "Total number of HTTP requests",
    ["route", "method", "response_status"],
)
flagsmith_http_server_request_duration_seconds = Histogram(
    "flagsmith_http_server_request_duration_seconds",
    "HTTP request duration in seconds",
    ["route", "method", "response_status"],
)
