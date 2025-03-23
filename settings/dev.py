import prometheus_client

# Settings expected by `mypy_django_plugin`
AWS_SES_REGION_ENDPOINT: str
PROMETHEUS_ENABLED: bool
SEGMENT_RULES_CONDITIONS_LIMIT: int
SENDGRID_API_KEY: str

# Settings required for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "common",
    }
}
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "common.core",
]
MIDDLEWARE = [
    "common.gunicorn.middleware.PrometheusGunicornLoggerMiddleware",
]
LOG_FORMAT = "json"
PROMETHEUS_HISTOGRAM_BUCKETS = prometheus_client.Histogram.DEFAULT_BUCKETS
ROOT_URLCONF = "common.core.urls"
TIME_ZONE = "UTC"
USE_TZ = True
