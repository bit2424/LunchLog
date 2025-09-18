# LunchLog API

Office Lunch Receipt Management and Recommendation System - REST API Backend

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
- `POST /api/v1/auth/token/` - Obtain auth token

### Receipts
- `GET /api/v1/receipts/` - List receipts
- `POST /api/v1/receipts/` - Create receipt
- `GET /api/v1/receipts/{id}/` - Get receipt detail
- `PUT /api/v1/receipts/{id}/` - Update receipt
- `DELETE /api/v1/receipts/{id}/` - Delete receipt

### Restaurants
- `GET /api/v1/restaurants/` - List restaurants
- `POST /api/v1/restaurants/` - Create restaurant
- `GET /api/v1/restaurants/{id}/` - Get restaurant detail
- `PUT /api/v1/restaurants/{id}/` - Update restaurant
- `DELETE /api/v1/restaurants/{id}/` - Delete restaurant

## Authentication

The API supports two authentication methods:

1. **Session Authentication**: For web applications
2. **Token Authentication**: For mobile apps and webhooks

### Obtaining a Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "your_username", "password": "your_password"}'
```

### Using the Token

```bash
curl -X GET http://localhost:8000/api/v1/receipts/ \
     -H "Authorization: Token your_token_here"
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

## Environment Variables

Copy `env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=postgresql://lunchlog:lunchlog123@localhost:5432/lunchlog

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `make test`
5. Check code quality: `make lint`
6. Format code: `make format`
7. Commit your changes: `git commit -am 'Add feature'`
8. Push to the branch: `git push origin feature-name`
9. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.