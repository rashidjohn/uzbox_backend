from pathlib import Path
from decouple import config
import dj_database_url
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent
(BASE_DIR / "logs").mkdir(exist_ok=True)

# ── Xavfsizlik ────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY")  # default yo'q — majburiy
DEBUG      = False  # har doim False, subclass override qiladi

# ── Ilovalar ──────────────────────────────────────────────
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "cloudinary",
    "cloudinary_storage",
    # local
    "apps.users",
    "apps.products",
    "apps.orders",
    "apps.payments",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF    = "config.urls"
AUTH_USER_MODEL = "users.User"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

# ── Database ──────────────────────────────────────────────
DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL", default="sqlite:///db.sqlite3"),
        conn_max_age=60,
        conn_health_checks=True,
    )
}

# ── Parol validatsiya ─────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Til va vaqt ───────────────────────────────────────────
LANGUAGE_CODE = "uz"
TIME_ZONE     = "Asia/Tashkent"
USE_I18N      = True
USE_TZ        = True

# ── Statik va media ───────────────────────────────────────
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL   = "/media/"
MEDIA_ROOT  = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Cloudinary ────────────────────────────────────────────
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME", default=""),
    "API_KEY":    config("CLOUDINARY_API_KEY",    default=""),
    "API_SECRET": config("CLOUDINARY_API_SECRET", default=""),
}
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ── DRF ───────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon":          "200/day",
        "user":          "2000/day",
        "login":         "5/minute",
        "register":      "3/minute",
        "checkout":      "20/hour",
        "promo_check":   "30/hour",
        "review":        "10/hour",
        "verify_email":  "5/hour",
        "password":      "5/hour",
        "wishlist":      "100/hour",
    },
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
}

# ── JWT ───────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS":  True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": True,
}

# ── Celery ────────────────────────────────────────────────
REDIS_URL              = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_BROKER_URL      = REDIS_URL
CELERY_RESULT_BACKEND  = REDIS_URL
CELERY_TIMEZONE        = "Asia/Tashkent"
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT  = ["json"]
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 daqiqa max

# ── Cache ─────────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND":  "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT":  300,
        "OPTIONS":  {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

# ── Email ─────────────────────────────────────────────────
# Email — subclass override qiladi (development=console, production=smtp)
EMAIL_BACKEND      = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST         = config("EMAIL_HOST", default="smtp.sendgrid.net")
EMAIL_PORT         = 587
EMAIL_USE_TLS      = True
EMAIL_HOST_USER    = "apikey"
EMAIL_HOST_PASSWORD = config("SENDGRID_API_KEY", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@uzbox.uz")

# ── To'lov tizimlari ──────────────────────────────────────
CLICK_SERVICE_ID  = config("CLICK_SERVICE_ID",  default="")
CLICK_MERCHANT_ID = config("CLICK_MERCHANT_ID", default="")
CLICK_SECRET_KEY  = config("CLICK_SECRET_KEY",  default="")
PAYME_MERCHANT_ID = config("PAYME_MERCHANT_ID", default="")
PAYME_SECRET_KEY  = config("PAYME_SECRET_KEY",  default="")

# ── Frontend URL (payments uchun) ─────────────────────────
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000")

# ── Logging ───────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {module}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class":     "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "class":     "logging.handlers.RotatingFileHandler",
            "filename":  str(BASE_DIR / "logs" / "django.log"),
            "maxBytes":  1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level":    "INFO",
    },
    "loggers": {
        "django": {
            "handlers":  ["console", "file"],
            "level":     "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers":  ["console", "file"],
            "level":     "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers":  ["console", "file"],
            "level":     "INFO",
            "propagate": False,
        },
    },
}

# ── Jazzmin admin UI ──────────────────────────────────────────
JAZZMIN_SETTINGS = {
    "site_title":        "UzBox Admin",
    "site_header":       "UzBox",
    "site_brand":        "UzBox",
    "site_logo":         None,
    "site_icon":         None,
    "welcome_sign":      "UzBox boshqaruv paneliga xush kelibsiz",
    "copyright":         "UzBox © 2025",
    "search_model":      ["users.User", "products.Product", "orders.Order"],
    "user_avatar":       "avatar",

    # Top menu
    "topmenu_links": [
        {"name": "Bosh sahifa",  "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Do'kon",       "url": "http://localhost:3000", "new_window": True},
        {"name": "API",          "url": "/api/", "new_window": True},
    ],

    # User menu (top right)
    "usermenu_links": [
        {"name": "Do'kon",  "url": "http://localhost:3000", "new_window": True, "icon": "fas fa-store"},
        {"model": "users.user"},
    ],

    # Sidebar menu
    "show_sidebar":          True,
    "navigation_expanded":   True,
    "hide_apps":             [],
    "hide_models":           [],
    "order_with_respect_to": [
        "users", "products", "orders", "payments", "notifications",
    ],

    "icons": {
        "auth":                    "fas fa-users-cog",
        "auth.user":               "fas fa-user",
        "auth.Group":              "fas fa-users",
        "users.User":              "fas fa-user-circle",
        "users.Address":           "fas fa-map-marker-alt",
        "products.Category":       "fas fa-tags",
        "products.Product":        "fas fa-box",
        "products.ProductImage":   "fas fa-images",
        "products.Review":         "fas fa-star",
        "products.Wishlist":       "fas fa-heart",
        "orders.Order":            "fas fa-shopping-bag",
        "orders.PromoCode":        "fas fa-ticket-alt",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    "related_modal_active": True,
    "custom_css":            "admin/custom.css",
    "custom_js":             None,
    "use_google_fonts_cdn":  True,
    "show_ui_builder":       False,

    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user":   "collapsible",
        "auth.group":  "vertical_tabs",
    },

    # Statistika kartalar
    "show_recent_actions":        True,
    "language_chooser":           False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text":     False,
    "footer_small_text":     False,
    "body_small_text":       False,
    "brand_small_text":      False,
    "brand_colour":          "navbar-orange",
    "accent":                "accent-orange",
    "navbar":                "navbar-white navbar-light",
    "no_navbar_border":      True,
    "navbar_fixed":          True,
    "layout_boxed":          False,
    "footer_fixed":          False,
    "sidebar_fixed":         True,
    "sidebar":               "sidebar-dark-orange",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style":  False,
    "sidebar_nav_flat_style":    False,
    "theme":                 "default",
    "dark_mode_theme":       None,
    "button_classes": {
        "primary":   "btn-primary",
        "secondary": "btn-secondary",
        "info":      "btn-info",
        "warning":   "btn-warning",
        "danger":    "btn-danger",
        "success":   "btn-success",
    },
}
