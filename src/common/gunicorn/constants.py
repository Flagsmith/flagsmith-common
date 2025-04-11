WSGI_DJANGO_ROUTE_ENVIRON_KEY = "wsgi.django_route"
HTTP_SERVER_RESPONSE_SIZE_DEFAULT_BUCKETS = (
    # 1 kB, 10 kB, 100 kB, 500 kB, 1 MB, 5 MB, 10 MB
    1 * 1024,
    10 * 1024,
    100 * 1024,
    500 * 1024,
    1 * 1024 * 1024,
    5 * 1024 * 1024,
    10 * 1024 * 1024,
    float("inf"),
)
