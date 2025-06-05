from datetime import time, timedelta

import dj_database_url
import prometheus_client
from environs import Env

from task_processor.task_run_method import TaskRunMethod

env = Env()

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
    },
]

# Settings expected by `mypy_django_plugin`
AWS_SES_REGION_ENDPOINT: str
SEGMENT_RULES_CONDITIONS_LIMIT: int
SENDGRID_API_KEY: str
PROMETHEUS_ENABLED = True

# Settings required for tests
SECRET_KEY = "test"
DATABASES = {
    "default": dj_database_url.parse(
        env(
            "DATABASE_URL",
            default="postgresql://postgres@localhost:5432/postgres",
        ),
    ),
    "task_processor": dj_database_url.parse(
        env(
            "TASK_PROCESSOR_DATABASE_URL",
            default="postgresql://postgres@localhost:5433/postgres",
        ),
    ),
}
TASK_PROCESSOR_DATABASES = ["default"]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "common.core",
    "task_processor",
]
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
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
TASK_BACKOFF_DEFAULT_DELAY_SECONDS = 5
TASK_DELETE_BATCH_SIZE = 2000
TASK_DELETE_INCLUDE_FAILED_TASKS = False
TASK_DELETE_RETENTION_DAYS = 15
TASK_DELETE_RUN_EVERY = timedelta(days=1)
TASK_DELETE_RUN_TIME = time(5, 0, 0)
TASK_PROCESSOR_MODE = env.bool("RUN_BY_PROCESSOR", default=False)
DOCGEN_MODE = env.bool("DOCGEN_MODE", default=False)
TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR

# To be used by test that depend on task processor to run tasks manually by
# calling `run_tasks`
TASK_PROCESSOR_MANUAL_MODE = env.bool("TASK_PROCESSOR_MANUAL_MODE", default=False)

# Avoid models.W042 warnings
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
