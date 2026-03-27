# Notification Service

Microservice for managing user notifications with internal API for other services.

## Features
- Internal API for creating notifications (service-to-service auth)
- External API for users: list, view, mark as read, soft delete
- Async SQLAlchemy + Alembic migrations
- JWT authentication (RS256)

## Quick Start
```bash
docker-compose up -d
alembic upgrade head
uvicorn src.main:app --reload