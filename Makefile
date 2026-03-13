# ShopUz Backend — qulay buyruqlar

# Development
run:
	python manage.py runserver

migrate:
	python manage.py migrate

migrations:
	python manage.py makemigrations

superuser:
	python manage.py createsuperuser

fixtures:
	python manage.py loaddata fixtures/demo_data.json

shell:
	python manage.py shell_plus

# Celery
celery:
	celery -A config.celery worker --loglevel=info

celery-beat:
	celery -A config.celery beat --loglevel=info

# Docker
docker-dev:
	docker-compose -f docker-compose.dev.yml up -d

docker-dev-stop:
	docker-compose -f docker-compose.dev.yml down

docker-prod:
	docker-compose up -d --build

docker-prod-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f backend

# Tests
test:
	python manage.py test

# Static
static:
	python manage.py collectstatic --noinput

# Tozalash
clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
