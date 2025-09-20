# LunchLog Makefile
# Office Lunch Receipt Management and Recommendation System - API Backend

# Default profile is development
PROFILE ?= dev

.PHONY: help up down migrate createsuperuser test lint format seed install dev-setup clean logs shell

# Default target
help: ## Show this help message
	@echo "LunchLog - Office Lunch Receipt Management and Recommendation System API"
	@echo "Available commands:"
	@echo "Current profile: $(PROFILE)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Docker commands
up: ## Start all containers with specified profile (dev or prod)
	docker compose --profile $(PROFILE) up -d
	@echo "Containers started with profile: $(PROFILE)"
	@if [ "$(PROFILE)" = "dev" ]; then\
		@echo "Waiting for database to be ready..."\
		@timeout 30 bash -c 'until docker compose exec -T db pg_isready -U lunchlog; do sleep 1; done' || echo "Database might not be ready yet"; fi
	
up-db-prod: ## Start only the database container
	docker compose --profile $(PROFILE) up -d db_prod
	@echo "Waiting for database to be ready..."
	@timeout 30 bash -c 'until docker compose exec -T db_prod pg_isready -U lunchlog; do sleep 1; done' || echo "Database might not be ready yet";

down: ## Stop and remove containers
	if [ "$(PROFILE)" = "prod" ]; then\
		docker compose --profile prod down; docker compose --profile dev down; fi
	@if [ "$(PROFILE)" = "dev" ]; then\
		docker compose --profile $(PROFILE) down; fi

build: ## Build or rebuild containers
	docker compose --profile $(PROFILE) build

restart: ## Restart all containers
	docker compose --profile $(PROFILE) restart

restart-backend: ## Restart only the backend container
	docker compose --profile $(PROFILE) restart backend

logs: ## Show container logs
	docker compose --profile $(PROFILE) logs -f

# Database commands
migrate: ## Run Django migrations
	python manage.py migrate

migrate-docker: ## Run Django migrations in Docker
	@if [ "$(PROFILE)" = "prod" ]; then\
		docker exec backend_prod python manage.py migrate; fi
	@if [ "$(PROFILE)" = "dev" ]; then\
		docker exec backend python manage.py migrate; fi

makemigrations: ## Create new Django migrations
	python manage.py makemigrations

makemigrations-docker: ## Create new Django migrations in Docker
	docker exec backend python manage.py makemigrations

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

# User management
createsuperuser: ## Create Django superuser
	python manage.py createsuperuser

createsuperuser-docker: ## Create Django superuser in Docker
	docker exec backend python manage.py createsuperuser

# Development commands
shell: ## Open Django shell
	python manage.py shell

runserver: ## Run Django development server
	python manage.py runserver

# Testing
test: ## Run all tests
	python -m pytest

test-coverage: ## Run tests with coverage report
	python -m pytest --cov=. --cov-report=html --cov-report=term-missing

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

dev-setup: install up migrate  ## Complete development setup to run locally
	@echo "Development environment setup complete!"
	@echo "You can now run 'make runserver' to start the development server"

dev-setup-docker: down build up migrate-docker ## Complete development setup in Docker
	@echo "Development environment setup complete!"
	@echo "You can now access the API at http://localhost:9000/api/v1/"

prod-setup: down build up-db-prod up migrate-docker ## Complete production setup in Docker
	@echo "Production environment setup complete!"
	@echo "You can now access the API at https://localhost/api/v1/"

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

# Monitoring
check: ## Run all checks (tests, linting, format)
	make format-check
	make lint
	make test