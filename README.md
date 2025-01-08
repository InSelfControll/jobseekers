# AI Job Search Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

## Overview

AI Job Search Platform is a sophisticated Flask-based web application that facilitates job searching and employer-candidate matching using AI technologies. The platform features SSO integration, custom domain support, and Telegram bot notifications.

### Architecture

The application follows a modular architecture with the following key components:

- **Flask Web Server**: Core application server
- **SQLAlchemy ORM**: Database management
- **Authentication System**: Supports both traditional and SSO login
- **Telegram Bot Integration**: Real-time notifications
- **SSL/TLS Support**: Secure communications
- **Custom Domain Handler**: Multi-tenant support

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-job-search.git
cd ai-job-search
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Component Documentation

### Core Components

- **ApplicationManager**: Manages application lifecycle and service initialization
- **Flask Application**: Handles HTTP requests and routing
- **Database Layer**: Manages data persistence and migrations
- **Authentication System**: Handles user authentication and session management
- **Telegram Bot**: Provides notification services

### Service Architecture

- **Extensions**: Modular service components (SSL, Database, Login)
- **Routes**: API endpoints and view functions
- **Models**: Database models and business logic
- **Security**: CSRF protection and security headers

## Configuration

The application uses a hierarchical configuration system:

1. **Environment Variables**: Primary configuration method
2. **Config Classes**: 
   - `DevelopmentConfig`
   - `ProductionConfig`
   - `TestingConfig`

### Key Configuration Options

- `FLASK_SECRET_KEY`: Application secret key
- `DATABASE_URL`: Database connection string
- `SSL_REQUIRED`: Enable/disable SSL
- `TELEGRAM_BOT_TOKEN`: Telegram bot credentials
- `SSO_ENABLED`: Enable/disable SSO functionality

## Development Setup

1. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

2. Run development server:
```bash
python main.py
```

3. Access the application:
```
http://localhost:3000
```

## Testing

1. Run unit tests:
```bash
python -m pytest tests/
```

2. Run integration tests:
```bash
python -m pytest tests/integration/
```

3. Generate coverage report:
```bash
coverage run -m pytest
coverage report
```

## Deployment

### Production Deployment

1. Set environment to production:
```bash
export FLASK_ENV=production
```

2. Configure production settings:
- Set secure session cookies
- Enable SSL
- Configure production database

3. Run using production server:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### Docker Deployment

```bash
docker build -t ai-job-search .
docker run -p 8000:8000 ai-job-search
```

## API Documentation

### Authentication Endpoints

- `POST /auth/login`: User login
- `POST /auth/logout`: User logout
- `POST /auth/register`: User registration

### Job Management

- `GET /jobs`: List jobs
- `POST /jobs`: Create job
- `GET /jobs/<id>`: Get job details
- `PUT /jobs/<id>`: Update job
- `DELETE /jobs/<id>`: Delete job

### Employer Routes

- `GET /employer/profile`: Get employer profile
- `PUT /employer/profile`: Update profile
- `POST /employer/domain`: Configure custom domain

## Contributing

1. Fork the repository
2. Create feature branch:
```bash
git checkout -b feature/your-feature-name
```

3. Commit changes:
```bash
git commit -m "Add your feature description"
```

4. Push to branch:
```bash
git push origin feature/your-feature-name
```

5. Create Pull Request

### Code Style

- Follow PEP 8 guidelines
- Write unit tests for new features
- Update documentation
- Use type hints
- Add docstrings for functions and classes

### Commit Guidelines

- Use clear, descriptive commit messages
- Reference issues in commits when applicable
- Keep commits focused and atomic

## License

This project is licensed under the MIT License - see the LICENSE file for details.