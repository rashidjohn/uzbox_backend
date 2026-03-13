from .base import *
from decouple import config

DEBUG         = False
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="").split(",")

# ── HTTPS xavfsizlik ──────────────────────────────────────
SECURE_SSL_REDIRECT            = True
SECURE_PROXY_SSL_HEADER        = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE          = True
SESSION_COOKIE_HTTPONLY        = True
CSRF_COOKIE_SECURE             = True
CSRF_COOKIE_HTTPONLY           = True
SECURE_HSTS_SECONDS            = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD            = True
SECURE_CONTENT_TYPE_NOSNIFF    = True
X_FRAME_OPTIONS                = "DENY"

# ── CORS ──────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS   = config("CORS_ALLOWED_ORIGINS", default="").split(",")
CORS_ALLOW_CREDENTIALS = True

# ── Database ──────────────────────────────────────────────
DATABASES["default"]["CONN_MAX_AGE"] = 60
DATABASES["default"]["OPTIONS"]      = {"sslmode": "require"}

# ── WhiteNoise — static fayllar (Nginx shart emas) ────────
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
USE_CLOUDINARY = config("CLOUDINARY_CLOUD_NAME", default="")
if USE_CLOUDINARY:
    STORAGES = {
        "default": {
            "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    # Cloudinary yo'q — lokal saqlash (Railway da vaqtinchalik)
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    MEDIA_URL  = "/media/"
    MEDIA_ROOT = "/tmp/media"  # Railway da /tmp ishlaydi

# ── Sentry — error tracking ───────────────────────────────
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment="production",
    )

# ── Logging ───────────────────────────────────────────────
LOGGING["root"]["level"]              = "WARNING"
LOGGING["loggers"]["apps"]["level"]   = "WARNING"
LOGGING["loggers"]["django"]["level"] = "ERROR"

# ── Email ────────────────────────────────────────────────
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")