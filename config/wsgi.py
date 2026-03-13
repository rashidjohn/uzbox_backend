import os
from django.core.wsgi import get_wsgi_application

# DJANGO_SETTINGS_MODULE env dan oladi — hardcoded emas
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
application = get_wsgi_application()
