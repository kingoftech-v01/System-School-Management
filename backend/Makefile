.PHONY: help build up down restart logs shell migrate makemigrations createsuperuser test lint format clean

help:
	@echo "Available commands:"
	@echo "  make build         - Build Docker images"
	@echo "  make up            - Start all services"
	@echo "  make down          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - View logs"
	@echo "  make shell         - Open Django shell"
	@echo "  make migrate       - Run migrations"
	@echo "  make makemigrations- Create migrations"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean up containers and volumes"
	@echo "  make create-tenant - Create a new tenant"
	@echo "  make demo-data     - Create demo data"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

shell:
	docker-compose exec web python manage.py shell

bash:
	docker-compose exec web bash

migrate:
	docker-compose exec web python manage.py migrate_schemas --shared
	docker-compose exec web python manage.py migrate_schemas

makemigrations:
	docker-compose exec web python manage.py makemigrations

createsuperuser:
	docker-compose exec web python manage.py createsuperuser

test:
	docker-compose exec web pytest

lint:
	docker-compose exec web flake8 .
	docker-compose exec web bandit -r . -x ./venv,./ENV,./tests

format:
	docker-compose exec web black .
	docker-compose exec web isort .

clean:
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

create-tenant:
	@read -p "Enter school name: " name; \
	read -p "Enter domain (e.g., school.localhost): " domain; \
	read -p "Enter admin email: " email; \
	docker-compose exec web python manage.py create_tenant --name "$$name" --domain "$$domain" --admin "$$email"

demo-data:
	@read -p "Enter tenant schema name: " tenant; \
	docker-compose exec web python manage.py create_demo_data --tenant "$$tenant"

# Production commands
prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

# Database backup
backup-db:
	@echo "Creating database backup..."
	docker-compose exec db pg_dump -U school_user school_db > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db:
	@read -p "Enter backup file path: " backup; \
	docker-compose exec -T db psql -U school_user school_db < "$$backup"

# Security scanning
security-check:
	docker-compose exec web safety check
	docker-compose exec web bandit -r . -f json -o security-report.json

# Collect static files
collectstatic:
	docker-compose exec web python manage.py collectstatic --noinput

# Translation
makemessages:
	docker-compose exec web python manage.py makemessages -a

compilemessages:
	docker-compose exec web python manage.py compilemessages
