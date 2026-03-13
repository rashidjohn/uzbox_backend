from .base import *

DEBUG = True

# ── Test uchun SQLite (PostgreSQL shart emas) ─────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME":   BASE_DIR / "test_db.sqlite3",
    }
}

# Test uchun tezroq parol hasher
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# In-memory cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Email test backend (haqiqiy email yuborilmaydi)
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Throttling o'chirish
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]   = {}

# Celery sinxron
CELERY_TASK_ALWAYS_EAGER    = True
CELERY_TASK_EAGER_PROPAGATES = True

# Cloudinary o'rniga local storage
STORAGES = {
    "default":    {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles":{"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Tezroq test uchun
MIGRATION_MODULES = {}