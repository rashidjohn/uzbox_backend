FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies — requirements/ papkasi ham ko'chiriladi
COPY requirements.txt .
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# logs papkasi
RUN mkdir -p logs

# Static files
RUN python manage.py collectstatic --noinput --settings=config.settings.production || true

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/uzb-secure-admin/login/ || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "config.wsgi:application"]