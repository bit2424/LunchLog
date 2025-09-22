# LunchLog API

Office Lunch Receipt Management and Recommendation System - REST API Backend

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Architecture](#project-architecture)
- [Data Schemas](#data-schemas)
- [API Endpoints](#api-endpoints)
  - [Authentication](#authentication)
  - [Receipts](#receipts)
  - [Restaurants](#restaurants)
- [Running the Project (Docker-first)](#running-the-project-docker-first)
- [Makefile Quick Reference](#makefile-quick-reference)
- [Environment Variables](#environment-variables)
- [Development](#development)
- [Major Decisions](#major-decisions)
- [Future Improvements](#future-improvements)

## Overview

LunchLog is a Django REST API to manage lunch receipts and recommend restaurants. Users can upload receipt images, link them to restaurants, and browse a curated database. Background jobs enrich restaurant data (e.g., via Google Places). Media files are stored locally in development and can be stored on AWS S3 in production.

## Features

- **REST API Backend**: Complete API for lunch receipt management
- **Receipt Management**: Upload, categorize, and track lunch receipts
- **Restaurant Database**: Maintain a database of preferred restaurants
- **Authentication**: Session and token-based authentication
- **Webhook Support**: Token-based authentication for external integrations

## Tech Stack

- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL
- **Testing**: pytest with coverage reporting
- **Code Quality**: black, isort, flake8
- **Containerization**: Docker Compose with profile-based deployments

## Project Architecture

- **Apps**: `users`, `receipts`, `restaurants`
- **API**: Django REST Framework routers under `/api/v1/`
- **Auth**: Session auth, DRF Token, and JWT (Simple JWT)
- **Background jobs**: Celery worker + Celery Beat with Redis broker
- **Database**: PostgreSQL
- **Storage**: Local filesystem in dev; AWS S3 (via `django-storages`) if S3 env vars are set
- **External API**: Google Places for restaurant enrichment (optional)

Data flow highlights:
- Receipt uploads store images under a user/date-based path. If S3 is configured, files go to your bucket.
- If a receipt has only `restaurant_name` and `address`, a background task attempts to enrich the linked `Restaurant` via Google Places.

## Data Schemas

Note: Simplified summary. See models for authoritative definitions.

- Receipt
  - id: integer
  - user: FK to `users.User`
  - date: date (YYYY-MM-DD)
  - price: decimal(10,2)
  - restaurant: FK to `restaurants.Restaurant` (nullable)
  - restaurant_name: string (nullable)
  - address: text (nullable)
  - image: file upload; image_url derived in responses
  - created_at / updated_at: timestamps

- Restaurant
  - id: UUID (primary key)
  - place_id: string (Google Places ID, unique)
  - name: string
  - address: text
  - latitude / longitude: float (nullable)
  - cuisines: many-to-many (if enabled)
  - rating: decimal(3,2) 0.00–5.00 (nullable)
  - updated_at: timestamp

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Poetry (optional, but recommended)

### Development Setup

1. **Clone and setup environment**:
```bash
git clone <repository-url>
cd lunchlog
make env  # Create .env from env.example
```

2. **Install dependencies**:
```bash
make install
```

3. **Start services with development profile**:
```bash
make up PROFILE=dev
```

This will:
- Start PostgreSQL container
- Run database migrations
- Start the development server with hot reloading

### Production Setup

1. **Start services with production profile**:
```bash
make up PROFILE=prod
```

This will:
- Start PostgreSQL container
- Run with Gunicorn server
- Enable production settings

### Available Profiles

The system supports different deployment profiles:

- **dev**: Development mode with hot reloading
  ```bash
  make up PROFILE=dev
  ```
- **prod**: Production mode with Gunicorn
  ```bash
  make up PROFILE=prod
  ```

You can also set the profile for your entire session:
```bash
export PROFILE=dev
make build
make up
make logs
```

### Docker Commands with Profiles

```bash
# Start containers with specific profile
make up PROFILE=dev

# Build containers for specific profile
make build PROFILE=prod

# View logs for current profile
make logs

# Stop containers for current profile
make down
```

### Manual Setup (Non-Docker)

If you prefer manual setup:

```bash
# Install dependencies
pip install -r requirements.txt
# OR with Poetry
poetry install

# Run migrations
make migrate

# Create superuser
make createsuperuser

# Start development server
make runserver
```

## Available Commands

Run `make help` to see all available commands:

```bash
make help           # Show help (displays current profile)
make up             # Start containers
make down           # Stop containers
make migrate        # Run migrations
make test           # Run tests
make lint           # Run linting
make format         # Format code
make seed           # Load initial data
```

## Project Structure

```
lunchlog/
├── apps/                  # Django applications
│   ├── receipts/          # Receipt management
│   └── restaurants/       # Restaurant database
├── lunchlog/              # Django project settings
│   ├── settings/          # Environment-specific settings
│   ├── authentication.py  # Custom auth classes
│   └── permissions.py     # Custom permissions
├── tests/                 # Project-wide tests
├── fixtures/              # Initial data fixtures
├── docker-compose.yml     # Container configuration
└── Makefile               # Development commands
```

## API Endpoints

### Authentication

- Session auth
  - `POST /api/v1/auth/signup/` - Create user and start session
  - `POST /api/v1/auth/login/` - Login and start session
- Token auth
  - `POST /api/v1/auth/token/` - Obtain DRF token
- JWT auth (Simple JWT)
  - `POST /api/v1/auth/jwt/create/`
  - `POST /api/v1/auth/jwt/refresh/`
  - `POST /api/v1/auth/jwt/verify/`

Examples:

```bash
# Create a user (session auth)
curl -X POST http://localhost:8000/api/v1/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "changeme123"}'

# Login (session auth)
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "changeme123"}'

# Obtain DRF token
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "changeme123"}'

# Create JWT
curl -X POST http://localhost:8000/api/v1/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "changeme123"}'
```

### Receipts

- `GET /api/v1/receipts/` - List receipts
- `POST /api/v1/receipts/` - Create receipt (multipart)
- `GET /api/v1/receipts/{id}/` - Get receipt detail
- `PUT /api/v1/receipts/{id}/` - Update receipt
- `DELETE /api/v1/receipts/{id}/` - Delete receipt

Examples:

```bash
# List (Token auth)
curl -X GET http://localhost:8000/api/v1/receipts/ \
  -H "Authorization: Token YOUR_TOKEN"

# Create (multipart). Provide restaurant_id OR restaurant_name + address
curl -X POST http://localhost:8000/api/v1/receipts/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "date=2025-09-19" \
  -F "price=12.50" \
  -F "restaurant_id=2c3c5fbc-2a5a-4b7f-8d52-6a3e9b5c9b02" \
  -F "image=@/absolute/path/to/receipt.jpg"

# OR name/address instead of restaurant_id
curl -X POST http://localhost:8000/api/v1/receipts/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "date=2025-09-19" \
  -F "price=12.50" \
  -F "restaurant_name=Pasta Place" \
  -F "address=123 Main St, City" \
  -F "image=@/absolute/path/to/receipt.jpg"
```

### Restaurants

- `GET /api/v1/restaurants/` - List restaurants
- `POST /api/v1/restaurants/` - Create restaurant
- `GET /api/v1/restaurants/{id}/` - Get restaurant detail
- `PUT /api/v1/restaurants/{id}/` - Update restaurant
- `DELETE /api/v1/restaurants/{id}/` - Delete restaurant

Examples:

```bash
# List (JWT)
ACCESS=$(curl -s -X POST http://localhost:8000/api/v1/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "changeme123"}' | jq -r .access)

curl -H "Authorization: Bearer $ACCESS" http://localhost:8000/api/v1/restaurants/

# Create
curl -X POST http://localhost:8000/api/v1/restaurants/ \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
        "name": "Pasta Place",
        "address": "123 Main St, City",
        "latitude": 40.7128,
        "longitude": -74.006,
        "cuisine_names": ["Italian"]
      }'
```

## Running the Project (Docker-first)

1. Initialize environment: `make env` then edit `.env`
2. Start services: `make up PROFILE=dev`
3. Run migrations: `make migrate-docker`
4. Create admin user: `make createsuperuser-docker`
5. Open API at `http://localhost:8000/api/v1/`

Production: `make up PROFILE=prod` (Gunicorn, production settings).

## Development

### Running Tests

```bash
make test              # Run all tests
make test-coverage     # Run with coverage report
```

### Code Quality

```bash
make lint              # Check code quality
make format            # Format code
make format-check      # Check formatting
```

### Database Management

```bash
make migrate           # Run migrations
make makemigrations    # Create new migrations
make reset-db          # Reset database (WARNING: destroys data)
```

## Makefile Quick Reference

```bash
make env                    # Initialize .env
make up PROFILE=dev         # Start db, backend, redis, celery, beat
make migrate-docker         # Run migrations in container
make createsuperuser-docker # Create admin user in container
make logs                   # Tail logs
make test                   # Run pytest in container
make down                   # Stop all containers (dev/prod)
```

## Environment Variables

Copy `env.example` to `.env` and configure as needed:

```env
# Database (Django defaults exist; override if needed)
DB_NAME=lunchlog
DB_USER=lunchlog
DB_PASSWORD=lunchlog123
DB_HOST=db
DB_PORT=5432

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# AWS S3 (optional; required for production media on S3)
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
AWS_S3_SIGNATURE_VERSION=s3v4

# Celery / Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Google Places (optional)
GOOGLE_PLACES_API_KEY=your-google-places-api-key
```

Notes:
- If `AWS_STORAGE_BUCKET_NAME` is set, uploaded receipt images are stored in S3.
- Redis is required for Celery jobs; started automatically via Docker Compose.

## Major Decisions

- **Django + DRF**: Fast delivery of a robust, well-documented REST API with batteries included (auth, permissions, serializers, viewsets).
- **PostgreSQL**: Reliable relational database with strong JSON support and indexing.
- **Celery + Redis**: Offload long-running/enrichment tasks (e.g., Google Places lookups) without blocking API requests.
- **AWS S3 for media**: Durable, cost-effective media storage; swap seamlessly via `django-storages`.
- **Accumulative stats tables**: When aggregating analytics, maintain accumulative tables to avoid recomputation on every request. Updates are appended/incremental via scheduled Celery tasks for predictable latency.

## Future Improvements

- **OCR for receipts**: Extract vendor, date, total, and line items from uploaded images. This can run asynchronously via Celery to keep requests fast.
- **Cuisine classification**: Train a lightweight classifier to better infer cuisine descriptors from names/menus; Google Maps types are often sparse or missing.
