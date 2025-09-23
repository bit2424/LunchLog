# LunchLog Makefile
# Office Lunch Receipt Management and Recommendation System - API Backend

# Default profile is development
PROFILE ?= dev

# Default target
help: ## Show this help message
	@echo "LunchLog - Office Lunch Receipt Management and Recommendation System API"
	@echo "Available commands:"
	@echo "Current profile: $(PROFILE)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Docker commands
up: ## Start all containers with specified profile (dev or prod)
	docker compose --profile $(PROFILE) up -d db
	@echo "Waiting for database to be ready..."
	@timeout 30 bash -c 'until docker compose exec -T db pg_isready -U lunchlog; do sleep 1; done' || echo "Database might not be ready yet";

	docker compose --profile $(PROFILE) up -d
	@echo "Containers started with profile: $(PROFILE)"

db-up: ## Start only the database container
	docker compose --profile $(PROFILE) up -d db
	@echo "Waiting for database to be ready..."
	@timeout 30 bash -c 'until docker compose exec -T db pg_isready -U lunchlog; do sleep 1; done' || echo "Database might not be ready yet";
	
down: ## Stop and remove containers
	docker compose --profile prod down; docker compose --profile dev down;

build: ## Build or rebuild containers
	docker compose --profile $(PROFILE) build

restart: ## Restart all containers
	docker compose --profile $(PROFILE) restart

restart-backend: ## Restart only the backend container
	docker compose --profile $(PROFILE) restart backend

logs: ## Show container logs
	docker compose --profile $(PROFILE) logs -f

migrate-docker: ## Run Django migrations in Docker
	docker exec backend python manage.py migrate;

makemigrations-docker: ## Create new Django migrations in Docker
	docker exec backend python manage.py makemigrations


add-demo-data: ## Add demo data to the database
	docker exec backend python manage.py seed_demo_data --fresh

reset-db: ## Reset database (WARNING: destroys all data)
	@echo "This will destroy all data. Are you sure? [y/N]"
	@read -r response; if [ "$$response" = "y" ] || [ "$$response" = "Y" ]; then \
		docker compose down -v; \
		docker compose up -d db; \
		sleep 5; \
		python manage.py migrate; \
	else \
		echo "Aborted."; \
	fi


createsuperuser-docker: ## Create Django superuser in Docker
	docker exec backend python manage.py createsuperuser

# Testing
test: ## Run all tests
	docker exec -e DJANGO_SETTINGS_MODULE=lunchlog.settings.test backend pytest -v

test-coverage: ## Run tests with coverage report
	docker compose exec -e DJANGO_SETTINGS_MODULE=lunchlog.settings.test backend pytest --cov=. --cov-report=html --cov-report=term-missing

# Code quality
lint: ## Run linting (flake8)
	python -m flake8 .

format: ## Format code with black and isort
	python -m black .
	python -m isort .

format-check: ## Check if code is properly formatted
	python -m black --check .
	python -m isort --check-only .

# Data management
seed: ## Load initial data fixtures
	@echo "Loading initial data..."
	python manage.py loaddata fixtures/restaurants.json || echo "No restaurant fixtures found"
	python manage.py loaddata fixtures/users.json || echo "No user fixtures found"
	@echo "Seeding completed"

# Installation and setup
install: ## Install Python dependencies
	pip install -r requirements.txt || echo "requirements.txt not found, using pyproject.toml"
	@if command -v poetry >/dev/null 2>&1; then \
		poetry install; \
	else \
		echo "Poetry not found. Install manually or use pip."; \
	fi

local-setup: install up migrate  ## Complete development setup to run locally
	@echo "Development environment setup complete!"
	@echo "You can now run 'make runserver' to start the development server"

docker-setup: down build up migrate-docker add-demo-data ## Complete development setup in Docker
	
	@echo "Development environment setup complete!"
	@if [ "$(PROFILE)" = "prod" ]; then \
		echo "You can now access the API at https://localhost/api/v1/"; \
	elif [ "$(PROFILE)" = "dev" ]; then \
		echo "You can now access the API at http://localhost:9000/api/v1/"; \
	else \
		echo "You can now access the API at http://localhost:9000/api/v1/"; \
	fi

# Utility commands
clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	docker compose down -v

generate-requirements: ## Generate requirements.txt from pyproject.toml
	@if command -v poetry >/dev/null 2>&1; then \
		poetry export -f requirements.txt --output requirements.txt --without-hashes; \
		echo "requirements.txt generated from pyproject.toml"; \
	else \
		echo "Poetry not found. Cannot generate requirements.txt"; \
	fi

# Environment variables
env: ## Create .env file from .env.example
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo ".env file created from env.example"; \
		echo "Please edit .env file with your settings"; \
	else \
		echo ".env file already exists"; \
	fi


precommit: format test ## Run all checks (tests, linting, format)