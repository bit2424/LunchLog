# LunchLog API

Office Lunch Receipt Management and Recommendation System - REST API Backend

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Architecture](#project-architecture)
- [Data Schemas](#data-schemas)
- [API Endpoints](#api-endpoints)
  - [API Documentation (Swagger)](#api-documentation-swagger)
  - [Authentication](#authentication)
  - [Receipts](#receipts)
  - [Restaurants](#restaurants)
  - [Recommendation System](#recommendation-system)
- [Running the Project (Docker-first)](#running-the-project-docker-first)
  - [For Development](#for-development)
  - [For Production](#for-production)
  - [Available Profiles](#available-profiles)
  - [Manual Setup (Non-Docker)](#manual-setup-non-docker)
- [Available Commands](#available-commands)
- [Makefile Quick Reference](#makefile-quick-reference)
- [Environment Variables](#environment-variables)
- [Development](#development)
  - [Running Tests](#running-tests)
  - [Code Quality](#code-quality)
  - [Database Management](#database-management)
- [Testing](#testing)
- [Major Decisions](#major-decisions)
- [Future Improvements](#future-improvements)

## Overview

LunchLog is a Django REST API to manage lunch receipts and recommend restaurants. Users can upload receipt images, link them to restaurants, and browse a curated database. Background jobs enrich restaurant data (e.g., via Google Places). Media files are stored locally in development and can be stored on AWS S3 in production.

## Project Structure

```
lunchlog/
├── apps/                  # Django applications
│   ├── users/             # User management
│   ├── receipts/          # Receipt management
│   └── restaurants/       # Restaurant database
├── lunchlog/              # Django project settings
│   ├── settings/          # Environment-specific settings
│   ├── authentication.py  # Custom auth classes
│   └── permissions.py     # Custom permissions
├── tests/                 # Project-wide tests
├── docker-compose.yml     # Container configuration
└── Makefile               # Development commands
```
## Prerequisites
- Docker and Docker Compose version 2.24.0+
- Poetry (optional, but recommended)
- Python 3.11+ (optional, to make local changes)
- Install make

## Quick Start

1. Initialize environment: `make env` then edit `.env`, even if you don't edit the `.env` file everything will work.
2. Start services: `make docker-setup PROFILE=dev`
4. Run tests: `make test-coverage`
5. API running at `http://localhost:9000/api/v1/`

## Features

- **REST API Backend**: Complete API for lunch receipt management
- **Receipt Management**: Upload, categorize, and track lunch receipts
- **Restaurant Database**: Maintain a database of preferred restaurants
- **Authentication**: Session and token-based authentication
- **Webhook Support**: Token-based authentication for external integrations

## Tech Stack

- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL
- **API Documentation**: Swagger UI & ReDoc (via drf-yasg)
- **Testing**: pytest with coverage reporting
- **Code Quality**: black, isort, flake8
- **Containerization**: Docker Compose with profile-based deployments

## Project Architecture

Infrastructure Diagram:

![Infrastructure Diagram](/documentation/Infra_Diagram.png)

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

ER diagram:

<p align="center">
  <img src="./documentation/ER_Diagram.png" height="900">
</p>

## Running the Project (Docker-first)

### For Development:
1. Initialize environment: `make env` then edit `.env`, even if you don't edit the `.env` file everything will work.
2. Start services: `make docker-setup`
3. Create admin user: `make createsuperuser-docker`
4. API running at `http://localhost:9000/api/v1/`

### For Production: 
1. You need to make sure to create the necessary SSL certificates and put them in the `deploy/certs` directory.
2. Run`make docker-setup PROFILE=prod` in step 2 above, and extra proxy container will be started to route to the production API.
3. API running at `https://localhost/api/v1/`

### Available Profiles

The system supports different deployment profiles:

- **dev**: Development mode
  ```bash
  make docker-setup PROFILE=dev
  ```
- **prod**: Production mode 
  ```bash
  make docker-setup PROFILE=prod
  ```

You can also set the profile for your entire session:
```bash
export PROFILE=dev
make docker-setup
make logs
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
make docker-setup   # Complete development setup in Docker
make up             # Start containers
make down           # Stop containers
make migrate        # Run migrations
make test           # Run tests
make test-coverage  # Run tests with coverage report
make lint           # Run linting
make format         # Format code
...
```

## API Endpoints

### API Documentation (Swagger)

Interactive API documentation is available via Swagger UI and ReDoc:

- **Swagger UI**: `http://localhost:9000/swagger/` (development) or `https://localhost/swagger/` (production)

The documentation includes:
- Interactive API explorer with "Try it out" functionality
- Remember to create a jwt token to use the api and put it in the "Authorization" header by clicking on the "Authorize" button. Don't forget to put the "Bearer " prefix in front of the token.
- You can use the default user "user@example.com" with password "changeme123" to test the api.
- Complete schema definitions for all models
- Authentication examples for all three auth methods
- Detailed documentation for the recommendation system endpoints

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

### Recommendation System

- `GET /api/v1/restaurants/recommendations/good/` - High-quality restaurant recommendations
- `GET /api/v1/restaurants/recommendations/cheap/` - Budget-friendly restaurant recommendations  
- `GET /api/v1/restaurants/recommendations/cuisine-match/` - Restaurants matching user's preferred cuisines
- `GET /api/v1/restaurants/recommendations/all/` - All recommendation types in a single response

#### Query Parameters

All recommendation endpoints support these optional parameters:
- `limit` - Number of recommendations to return (default: 20 for individual types, 10 for all)
- `radius` - Search radius in meters around frequent locations (default: 2000)
- `search_limit` - Max results per location search (default: 20)

#### Examples

```bash
# Get good restaurant recommendations
curl -H "Authorization: Bearer $ACCESS" \
  "http://localhost:8000/api/v1/restaurants/recommendations/good/?limit=10&radius=1500"

# Get budget-friendly recommendations
curl -H "Authorization: Bearer $ACCESS" \
  "http://localhost:8000/api/v1/restaurants/recommendations/cheap/?limit=15"

# Get cuisine-matched recommendations
curl -H "Authorization: Bearer $ACCESS" \
  "http://localhost:8000/api/v1/restaurants/recommendations/cuisine-match/"

# Get all recommendation types
curl -H "Authorization: Bearer $ACCESS" \
  "http://localhost:8000/api/v1/restaurants/recommendations/all/?limit=5"
```

#### Response Format

Each recommendation includes:
- Restaurant details (name, address, rating, etc.)
- Recommendation type and reason
- User context (frequent restaurants, preferred cuisines)
- Google Places enrichment data when available

Example response:
```json
{
  "recommendation_type": "good",
  "count": 5,
  "recommendations": [
    {
      "place_id": "ChIJ...",
      "name": "Amazing Bistro",
      "rating": 4.8,
      "price_level": 2,
      "vicinity": "123 Food St, City",
      "cuisines": ["French", "European"],
      "recommendation_type": "good",
      "business_status": "OPERATIONAL"
    }
  ],
  "user_context": {
    "frequent_restaurants": [
      {"name": "Regular Spot", "visit_count": 15}
    ],
    "preferred_cuisines": [
      {"name": "Italian", "visit_count": 8}
    ]
  }
}
```

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

## Testing

This project uses pytest. We maintain fast, isolated unit tests and broader integration tests, mock external systems by default, and provide an opt-in test that can hit real external APIs when needed.

We also added a code coverage report to the tests, currently the tests only pass with at least 80% coverage, which is currently achived.

### Test types

- Unit tests: Validate small, isolated logic (serializers, utilities, services). All I/O and externals are mocked.
- Integration tests: Exercise end-to-end flows across Django, DRF, PostgreSQL, and Celery. Celery runs in eager mode in tests so task results are asserted immediately.

### Mocking external systems

External dependencies (e.g., Google Places) are mocked using `unittest.mock.patch` to keep tests deterministic and fast. We also mock Celery enqueues where appropriate.

```python
from unittest import mock

with mock.patch("apps.restaurants.tasks.GooglePlacesService") as MockService:
    svc = MockService.return_value
    svc.find_place_from_text.return_value = {"candidates": [...]}
    svc.fetch_restaurant_details.return_value = {"result": {...}}

with mock.patch("apps.restaurants.tasks.update_restaurant_info.delay") as mock_task:
    resp = auth_client.post("/api/v1/receipts/", data, format="multipart")
    mock_task.assert_called_once()
```

### Live external test (opt‑in)

There is a single test marked `external` that can call the real Google Places API to verify end-to-end enrichment. It is skipped unless `GOOGLE_PLACES_API_KEY` is provided.

Run it explicitly (Docker):

```bash
# Start services (if not running)
make docker-setup
```

### Selective runs

```bash
# All tests (inside Docker)
make test

# Only integration tests
docker compose exec backend pytest -m integration -q

# Run only external tests
docker compose exec backend bash -lc \
  'export GOOGLE_PLACES_API_KEY=your-key && pytest -m external -q'

# Coverage
make test-coverage
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
