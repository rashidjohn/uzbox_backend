import os
from celery import Celery

# DJANGO_SETTINGS_MODULE env dan oladi — hardcoded emas
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("uzbox")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
