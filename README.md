# Auth Service

Production-ready микросервис аутентификации и авторизации на базе **FastAPI** (Python 3.13).  
Реализует регистрацию пользователей, выдачу JWT-токенов, управление разрешениями и полный набор production-инструментов: метрики Prometheus, health-checks, трейсинг запросов, rate-limiting и наблюдаемость через Grafana.

## Возможности

- **Python 3.13** + **FastAPI** с полной поддержкой async/await
- **JWT-аутентификация** — access/refresh токены, Refresh Token Rotation
- **Argon2id** — безопасное хеширование паролей
- **Dishka** — внедрение зависимостей (DI)
- **psycopg3** — асинхронный пул подключений к PostgreSQL
- **Redis** (опционально) — хранилище refresh-токенов; отключается через `REDIS__ENABLED=false`
- **httpx** — HTTP-клиент для внешних запросов (пул соединений, таймауты)
- **Prometheus** метрики (`/metrics`)
- **Health checks** (liveness, readiness, detailed)
- **X-Request-ID** — трейсинг запросов
- **Rate Limiting** — защита от перебора
- **Timeout middleware** — ограничение времени обработки запроса
- **Graceful shutdown** — корректное закрытие Dishka-контейнера и коннекторов
- **Глобальная обработка исключений**
- **yoyo-migrations** — управление схемой базы данных
- **Prometheus + Grafana** — мониторинг и дашборды

---

## Быстрый старт

### 1. Переменные окружения

```bash
cp .env.example .env
# Отредактируйте .env, заполнив POSTGRES__* и другие обязательные переменные
```

### 2. Установка зависимостей

```bash
make install
# или
uv sync
```

### 3. Запуск через Docker Compose (рекомендуется)

Поднимает PostgreSQL, Redis, само приложение, Prometheus и Grafana:

```bash
docker-compose up --build -d
# или
make docker_up
```

### 4. Применение миграций

```bash
make migrate
```

### 5. Запуск сервера для разработки

```bash
make run
```

Сервер доступен по адресу: `http://localhost:8000`  
Swagger UI (в debug-режиме): `http://localhost:8000/docs`

---

## Продакшн-запуск

```bash
make run-prod
# или
uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --workers 4 --no-access-log --log-config logging_config.json
```

### Расчёт пула подключений (multi-worker)

При нескольких воркерах суммарное число соединений:

```
Итого Postgres = workers × POSTGRES__MAX_CONNECTION
Итого Redis    = workers × REDIS__MAX_CONNECTIONS
```

**Пример:** 4 воркера, `MAX_CONNECTION=10`, `REDIS__MAX_CONNECTIONS=10` → 40 соединений к Postgres + 40 к Redis.  
Формула для `MAX_CONNECTION`: `(pg_max_connections - 3) / workers`.

---

## API Эндпоинты

### Аутентификация (`/api/v1/auth`)

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/v1/auth/login` | Вход — возвращает access + refresh токены |
| `POST` | `/api/v1/auth/token` | OAuth2-совместимый эндпоинт (для Swagger UI) |
| `POST` | `/api/v1/auth/refresh` | Обновление пары токенов (Refresh Token Rotation) |
| `POST` | `/api/v1/auth/logout` | Выход — инвалидация refresh-токена |

### Пользователи (`/api/v1/users`) — требуется авторизация

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/v1/users/` | Создать пользователя (пароль хешируется через Argon2id) |
| `GET` | `/api/v1/users/me` | Профиль текущего пользователя с разрешениями |
| `GET` | `/api/v1/users/{username}` | Получить пользователя по username |

### Разрешения (`/api/v1/permissions`) — требуется авторизация

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/v1/permissions/` | Создать разрешение (требует `manage_permissions`) |
| `GET` | `/api/v1/permissions/` | Список всех разрешений |
| `GET` | `/api/v1/permissions/{code}` | Получить разрешение по коду |
| `POST` | `/api/v1/permissions/assign` | Назначить разрешение пользователю |
| `DELETE` | `/api/v1/permissions/revoke` | Отозвать разрешение у пользователя |
| `GET` | `/api/v1/permissions/user/{user_id}` | Разрешения конкретного пользователя |

### Health Checks

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/health/liveness` | Сервис жив (всегда `ok`) |
| `GET` | `/health/readiness` | Все зависимости доступны (Postgres, Redis) |
| `GET` | `/health/detailed` | Детальная информация + статистика пулов |

### Метрики

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/metrics` | Prometheus-метрики |

**Доступные метрики:**
- `http_requests_total` — всего запросов (метод, эндпоинт, статус)
- `http_request_duration_seconds` — гистограмма латентности
- `http_requests_in_progress` — запросы в обработке прямо сейчас

---

## Структура проекта

```
auth/
├── app/
│   ├── main.py                        # Фабрика FastAPI-приложения
│   ├── configuration/
│   │   └── providers/                 # Dishka DI-провайдеры
│   │       ├── settings.py            # Настройки
│   │       ├── connectors.py          # Postgres / Redis коннекторы
│   │       ├── repository.py          # Репозитории
│   │       ├── service.py             # Сервисный слой
│   │       └── client.py             # HTTP-клиент
│   ├── internal/
│   │   ├── models/                    # Pydantic-схемы запросов/ответов
│   │   │   ├── user/
│   │   │   ├── token/
│   │   │   └── permissions/
│   │   ├── repository/                # Слой доступа к данным
│   │   │   ├── postgres/              # PostgreSQL-репозитории
│   │   │   └── redis/                 # Redis-репозитории
│   │   ├── routes/                    # API-роуты
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   └── permissions.py
│   │   ├── service/                   # Бизнес-логика
│   │   │   ├── token.py
│   │   │   ├── user.py
│   │   │   └── permission.py
│   │   └── pkg/
│   │       └── middlewares/           # Middleware (auth, rate limit, timeout, prometheus…)
│   └── pkg/
│       ├── client/                    # HTTP-клиент (httpx)
│       ├── connectors/                # Коннекторы Postgres / Redis
│       ├── logger/                    # Настройка логирования
│       ├── models/                    # Базовые модели и исключения
│       └── settings/                  # Pydantic-настройки
├── migrations/                        # yoyo-миграции
├── scripts/
│   └── migrate.py                     # Скрипт применения миграций
├── tests/
│   ├── unit/                          # Юнит-тесты
│   ├── integration/                   # Интеграционные тесты
│   └── load/                          # Нагрузочные тесты (Locust)
├── docs/
│   ├── prometheus.yml                 # Конфигурация Prometheus
│   └── prometheus_rules.yml           # Правила алертинга
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
└── logging_config.json
```

---

## Конфигурация

Переменные окружения задаются с разделителем `__` (например, `POSTGRES__HOST`).

### API

| Переменная | Умолчание | Описание |
|------------|-----------|----------|
| `API__HOST` | `0.0.0.0` | Хост сервера |
| `API__PORT` | `8000` | Порт сервера |
| `API__WORKERS` | `1` | Число воркеров uvicorn |
| `API__DEBUG` | `false` | Режим отладки |
| `API__DOCS_ENABLED` | `true` | Включить Swagger UI / ReDoc |
| `API__REQUEST_TIMEOUT` | `30` | Таймаут запроса (сек) |
| `API__GRACEFUL_SHUTDOWN_TIMEOUT` | `30` | Таймаут graceful shutdown (сек) |
| `API__CORS_ORIGINS` | `["*"]` | Разрешённые CORS-источники |
| `API__RATE_LIMIT_ENABLED` | `false` | Включить rate limiting |
| `API__RATE_LIMIT_REQUESTS` | `100` | Макс. запросов в окне |
| `API__RATE_LIMIT_WINDOW` | `60` | Размер окна rate limit (сек) |

### PostgreSQL

| Переменная | Умолчание | Описание |
|------------|-----------|----------|
| `POSTGRES__HOST` | обязательно | Хост базы данных |
| `POSTGRES__PORT` | обязательно | Порт базы данных |
| `POSTGRES__USER` | обязательно | Пользователь |
| `POSTGRES__PASSWORD` | обязательно | Пароль |
| `POSTGRES__DATABASE_NAME` | обязательно | Название базы |
| `POSTGRES__MIN_CONNECTION` | `2` | Минимальный размер пула (на воркер) |
| `POSTGRES__MAX_CONNECTION` | `10` | Максимальный размер пула (на воркер) |
| `POSTGRES__TIMEOUT` | `30` | Таймаут получения соединения (сек) |
| `POSTGRES__STATEMENT_TIMEOUT` | `30000` | Таймаут запроса к БД (мс) |

### Redis (опционально)

| Переменная | Умолчание | Описание |
|------------|-----------|----------|
| `REDIS__ENABLED` | `false` | Включить Redis-коннектор |
| `REDIS__URL` | `redis://localhost:6379/0` | Redis URL (путь = индекс БД 0–15) |
| `REDIS__SOCKET_TIMEOUT` | `5.0` | Socket таймаут (сек) |
| `REDIS__MAX_CONNECTIONS` | `10` | Макс. соединений в пуле (на воркер) |

### Логирование

| Переменная | Умолчание | Описание |
|------------|-----------|----------|
| `LOG_FORMAT` | `text` | Формат: `text` (dev) или `json` (prod / ELK / Loki) |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

---

## Миграции

```bash
make migrate           # Применить миграции
make migrate-rollback  # Откатить все миграции
make migrate-reload    # Откатить и применить заново
make migrate-list      # Посмотреть статус миграций
```

Файлы миграций хранятся в директории `migrations/`.

---

## Разработка

### Команды Makefile

```bash
make run          # Запуск dev-сервера с hot-reload
make run-dev      # Запуск через run.py (uv run)
make run-prod     # Запуск prod-сервера (multi-worker)
make docker_up    # Поднять всё через Docker Compose

make fmt          # Форматирование кода (autoflake, isort, black, docformatter)
make check        # Линтинг (flake8, bandit, safety)
make mypy         # Проверка типов
make clean        # Удалить __pycache__
```

### Тесты

```bash
# Юнит-тесты
pytest tests/unit/

# Интеграционные тесты (требуется запущенный Postgres)
pytest tests/integration/

# Нагрузочные тесты (Locust)
locust -f tests/load/locustfile.py
```

---

## Мониторинг

После запуска через `docker-compose up`:

| Сервис | URL |
|--------|-----|
| Auth API | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` (admin / admin) |

---

## Стек технологий

| Категория | Библиотека |
|-----------|-----------|
| Web-фреймворк | FastAPI |
| ASGI-сервер | Uvicorn |
| DI-контейнер | Dishka |
| База данных | PostgreSQL 16 + psycopg3 |
| Кеш / хранилище токенов | Redis 7 |
| HTTP-клиент | httpx |
| Валидация | Pydantic v2 |
| Настройки | pydantic-settings |
| Хеширование паролей | Argon2-cffi |
| JWT | PyJWT |
| Миграции | yoyo-migrations |
| Метрики | prometheus-client |
| Тестирование | pytest, pytest-asyncio, httpx |
| Форматирование | black, isort, autoflake, ruff |
| Линтинг | flake8, bandit, safety |
