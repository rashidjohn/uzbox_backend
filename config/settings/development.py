from .base import *
from decouple import config

DEBUG         = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]
SECRET_KEY    = config("SECRET_KEY", default="django-dev-secret-key-not-for-production-use")

# ── Dev-only apps
INSTALLED_APPS += ["django_extensions"]

# ── SQLite (development) ──────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME":   BASE_DIR / "db.sqlite3",
    }
}

# ── Email — consolega chiqarish ───────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ── Media — local saqlash ─────────────────────────────────
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
MEDIA_ROOT = BASE_DIR / "media"

# ── CORS ──────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
# Local network (masalan, telefonda test)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://192\.168\.\d{1,3}\.\d{1,3}(:\d+)?$",
    r"^http://10\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$",
]
CORS_ALLOW_CREDENTIALS = True

# ── Cache — DummyCache (development) ─────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# ── Celery — task larni sync bajarish (Celery server shart emas) ──
CELERY_TASK_ALWAYS_EAGER  = True
CELERY_TASK_EAGER_PROPAGATES = True

# ── Logging — debug ───────────────────────────────────────
LOGGING["root"]["level"] = "DEBUG"
LOGGING["loggers"]["apps"]["level"] = "DEBUG"

# ── Django debug toolbar (ixtiyoriy) ─────────────────────
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
# INTERNAL_IPS = ["127.0.0.1"]
