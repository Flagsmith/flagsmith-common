import prometheus_client

from common.prometheus import Histogram

http_server_requests_total = prometheus_client.Counter(
    "http_server_requests_total",
    "Total number of HTTP requests",
    ["route", "method", "response_status"],
)
http_server_request_duration_seconds = Histogram(
    "http_server_request_duration_seconds",
    "HTTP request duration in seconds",
    ["route", "method", "response_status"],
)
