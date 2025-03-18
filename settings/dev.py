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

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
SENDGRID_API_KEY = ""
AWS_SES_REGION_ENDPOINT = ""
SEGMENT_RULES_CONDITIONS_LIMIT = 0
