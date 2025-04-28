import re

WSGI_EXTRA_PREFIX = "flagsmith."
WSGI_EXTRA_SUFFIX_TO_CATEGORY = {
    "i": "request_headers",
    "o": "response_headers",
    "e": "environ_variables",
}
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

wsgi_extra_key_regex = re.compile(
    r"^{(?P<key>[^}]+)}(?P<suffix>[%s])$" % "".join(WSGI_EXTRA_SUFFIX_TO_CATEGORY)
)
