# Notification Service 

Микросервис управления уведомлениями пользователей с внутренним API для взаимодействия с другими сервисами. Построен на **FastAPI** с асинхронной архитектурой и чистой структурой проекта.

---

## Особенности

### Функционал
- **Внутренний API** для создания уведомлений (service-to-service аутентификация через JWT RS256)
- **Пользовательские эндпоинты**: просмотр списка, получение по ID, отметка как прочитанное, мягкое удаление
- **Статусы уведомлений**: `pending` → `sent` → `delivered` / `failed`
- **Soft delete**: уведомления не удаляются физически, а помечаются `deleted_at`
- **Асинхронная работа с БД**: SQLAlchemy 2.0 + asyncpg
- **Миграции**: Alembic с поддержкой async
- **Валидация данных**: Pydantic v2 с `ConfigDict(from_attributes=True)`

### Архитектура
```
src/
├── api/v1/
│   ├── notifications/     # Основной модуль уведомлений
│   │   ├── models.py      # SQLAlchemy модели
│   │   ├── schemas.py     # Pydantic схемы (request/response)
│   │   ├── repository.py  # Слой доступа к данным
│   │   ├── service.py     # Бизнес-логика
│   │   ├── router.py      # API маршруты
│   │   ├── dependencies.py # DI для сервисов
│   │   └── exceptions.py  # Кастомные ошибки с HTTP-метаданными
│   └── auth/
│       └── dependencies.py # JWT верификация для сервисов
├── config.py              # Настройки через pydantic-settings
├── database.py            # Инициализация async SQLAlchemy
└── main.py                # Точка входа FastAPI приложения
```

---

## Технологический стек

| Компонент | Технология |
|-----------|-----------|
| **Фреймворк** | FastAPI 0.109+ |
| **База данных** | PostgreSQL 14+ |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Миграции** | Alembic |
| **Валидация** | Pydantic v2 |
| **Аутентификация** | PyJWT (RS256) |
| **Тестирование** | pytest + pytest-asyncio + httpx |
| **Сервер** | uvicorn |

---

## API Endpoints

Все эндпоинты защищены аутентификацией через JWT (заголовок `Authorization: Bearer <token>`).

### Service-to-Service (внутренние)

| Метод | Путь | Описание | Статусы |
|-------|------|----------|---------|
| `POST` | `/api/v1/notifications/create_notification` | Создать новое уведомление | `201 Created` |

**Request Body:**
```json
{
  "recipient_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Новое сообщение",
  "body": "Текст уведомления..."
}
```

**Response:**
```json
{
  "id": "uuid",
  "recipient_id": "uuid",
  "title": "Новое сообщение",
  "body": "Текст уведомления...",
  "status": "pending",
  "is_read": false,
  "created_at": "2024-01-15T10:30:00Z",
  "deleted_at": null
}
```

### User-Facing (пользовательские)

| Метод | Путь | Описание | Статусы |
|-------|------|----------|---------|
| `GET` | `/api/v1/notifications/get_notification/{id}` | Получить уведомление по ID | `200 OK` / `404 Not Found` |
| `GET` | `/api/v1/notifications/get_user_notifications/{user_id}` | Список заголовков уведомлений пользователя | `200 OK` |
| `PATCH` | `/api/v1/notifications/mark_notification_as_read/{id}` | Отметить как прочитанное | `200 OK` / `404 Not Found` |
| `DELETE` | `/api/v1/notifications/delete_notification/{id}` | Мягкое удаление уведомления | `204 No Content` / `404 Not Found` |

---

## Установка и запуск

### Предварительные требования
- Python 3.11+
- PostgreSQL 14+
- Docker (опционально, для БД)

### 1. Клонирование и установка зависимостей
```bash
git clone <repository>
cd notification-service
pip install -r requirements.txt
```

### 2. Настройка окружения
Создайте файл `.env` в корне проекта:

```env
# Database
DB__DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/notifications
DB__ECHO=false

# JWT Auth (RS256)
AUTH_JWT__ALGORITHM=RS256
AUTH_JWT__PRIVATE_KEY_PATH=./src/certs/private.pem
AUTH_JWT__PUBLIC_KEY_PATH=./src/certs/public.pem
AUTH_JWT__ACCESS_TOKEN_EXPIRE_MINUTES=15
```

> **Важно**: Сгенерируйте RSA-ключи для JWT:
> ```bash
> openssl genrsa -out src/certs/private.pem 2048
> openssl rsa -in src/certs/private.pem -pubout -out src/certs/public.pem
> ```

### 3. Применение миграций
```bash
alembic upgrade head
```

### 4. Запуск сервера
```bash
# Development mode с авто-релоадом
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Запуск через Docker (опционально)
```bash
# docker-compose.yml (пример)
version: '3.8'
services:
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: notifications
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

---

## Тестирование

Проект покрыт модульными и интеграционными тестами с использованием `pytest`.

### Запуск тестов
```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest --cov=src --cov-report=html

# Только тесты уведомлений
pytest tests/notifications/ -v
```

### Особенности тестовой инфраструктуры
- Отдельная тестовая БД (`notifications_test`)
- Автоматический откат транзакций после каждого теста (`ROLLBACK`)
- Моки аутентификации через `app.dependency_overrides`
- Async-фикстуры с `pytest-asyncio`

### Структура тестов
```
tests/
├── conftest.py              # Глобальные фикстуры
└── notifications/
    ├── test_notifications_api.py       # API-тесты (TestClient)
    ├── test_notifications_service.py   # Тесты бизнес-логики
    ├── test_notifications_repository.py # Тесты слоя данных
    └── test_notifications_model.py     # Тесты моделей
```

---

## Аутентификация

Сервис использует **асимметричный JWT (RS256)** для аутентификации между сервисами:

1. Внешний сервис подписывает токен **приватным ключом**
2. Notification Service проверяет подпись **публичным ключом**
3. Токен передаётся в заголовке: `Authorization: Bearer <jwt_token>`

> Для разработки можно отключить проверку через `app.dependency_overrides` (см. `tests/conftest.py`)

---

## Модель данных

### Таблица `notifications`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID (PK) | Уникальный идентификатор |
| `recipient_id` | UUID (index) | ID получателя (из user-service) |
| `title` | VARCHAR(255) | Заголовок уведомления |
| `body` | TEXT | Текст уведомления |
| `status` | VARCHAR(50) | Статус: `pending`/`sent`/`delivered`/`failed` |
| `is_read` | BOOLEAN | Флаг прочтения |
| `deleted_at` | TIMESTAMP (index) | Дата мягкого удаления (NULL = активно) |
| `created_at` | TIMESTAMP | Дата создания (auto) |

---

## Миграции (Alembic)

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Add new field"

# Применить миграции
alembic upgrade head

# Откатить на одну миграцию
alembic downgrade -1

# Просмотр истории
alembic history
```

> Конфигурация `alembic/env.py` автоматически подгружает `DATABASE_URL` из `.env`

---

## Структура ответа об ошибках

```json
{
  "detail": "Notification <uuid> not found"
}
```

| Статус | Причина |
|--------|---------|
| `400` | Ошибка валидации входных данных |
| `401` | Неверный или отсутствующий JWT-токен |
| `404` | Уведомление или пользователь не найдены |
| `500` | Внутренняя ошибка сервера |

---

## 📄 Лицензия

GPL-3.0 license