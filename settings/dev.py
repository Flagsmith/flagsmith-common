SENDGRID_API_KEY: str
AWS_SES_REGION_ENDPOINT: str
SEGMENT_RULES_CONDITIONS_LIMIT: int

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "common",
    }
}
