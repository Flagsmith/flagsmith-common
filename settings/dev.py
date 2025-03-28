from datetime import time, timedelta

import dj_database_url
import prometheus_client
from environs import Env

from task_processor.task_run_method import TaskRunMethod

env = Env()

# Settings expected by `mypy_django_plugin`
AWS_SES_REGION_ENDPOINT: str
SEGMENT_RULES_CONDITIONS_LIMIT: int
SENDGRID_API_KEY: str
PROMETHEUS_ENABLED = True

# Settings required for tests
DATABASES = {
    "default": dj_database_url.parse(
        env(
            "DATABASE_URL",
            default="postgresql://postgres:password@localhost:5432/flagsmith",
        )
    )
}
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "common.core",
    "task_processor",
]
MIDDLEWARE = [
    "common.gunicorn.middleware.RouteLoggerMiddleware",
]
LOG_FORMAT = "json"
PROMETHEUS_HISTOGRAM_BUCKETS = prometheus_client.Histogram.DEFAULT_BUCKETS
ROOT_URLCONF = "common.core.urls"
TIME_ZONE = "UTC"
USE_TZ = True

ENABLE_CLEAN_UP_OLD_TASKS = True
ENABLE_TASK_PROCESSOR_HEALTH_CHECK = True
RECURRING_TASK_RUN_RETENTION_DAYS = 15
TASK_DELETE_BATCH_SIZE = 2000
TASK_DELETE_INCLUDE_FAILED_TASKS = False
TASK_DELETE_RETENTION_DAYS = 15
TASK_DELETE_RUN_EVERY = timedelta(days=1)
TASK_DELETE_RUN_TIME = time(5, 0, 0)
TASK_PROCESSOR_MODE = False
TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR

# Avoid models.W042 warnings
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
