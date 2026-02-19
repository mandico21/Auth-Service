# pattern-service

Production-ready FastAPI microservice scaffold (Python 3.13) with PostgreSQL, optional Redis, Dishka DI, and observability.

## Features
- **Python 3.13** (version pinned in template)
- **FastAPI** with async support
- **Dishka** dependency injection
- **psycopg3** async PostgreSQL connection pool
- **Redis** (optional) — connector and DI provider; no-op when `REDIS__ENABLED=false`
- **httpx** — HTTP client for outbound requests (connection pooling, timeouts)
- **Prometheus** metrics (`/metrics`)
- **Health checks** (liveness, readiness, detailed with Postgres + Redis)
- **Request tracing** (X-Request-ID)
- **Request timeout** middleware
- **Lifespan** — graceful shutdown (Dishka container and connectors closed)
- **Global exception handling**
- **Retry logic** for database operations
- **yoyo-migrations** for schema management

## Quick Start

1. Copy environment file and configure:
```bash
cp .env.example .env
```

2. Install dependencies:
```bash
make install
# or
uv sync
```

3. Run migrations:
```bash
make migrate
```

4. Start development server:
```bash
make run
```

Server runs at `http://localhost:8000`

## Production Deployment

### With uvicorn workers:
```bash
make run-prod
# or
uvicorn app.main:create_app --host 0.0.0.0 --port 8000 --workers 4
```

### With gunicorn (recommended):
```bash
make run-gunicorn
# or
gunicorn app.main:create_app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 30 \
    --graceful-timeout 30
```
Use `--graceful-timeout` equal to or greater than `API__GRACEFUL_SHUTDOWN_TIMEOUT` so workers can close connectors before being killed.

### Connection limits (multi-worker)
With multiple workers, total DB/Redis connections = **workers × (POSTGRES__MAX_CONNECTION + REDIS__MAX_CONNECTIONS)** per instance. Example: 4 workers, `MAX_CONNECTION=20`, `REDIS__MAX_CONNECTIONS=10` → up to 80 Postgres + 40 Redis connections. Set server-side limits (e.g. `max_connections` in Postgres) accordingly.

## Health Checks

| Endpoint | Description |
|----------|-------------|
| `GET /health/liveness` | Always returns `ok` if app is running |
| `GET /health/readiness` | Checks all dependencies (Postgres, Redis if enabled) |
| `GET /health/detailed` | Detailed health with pool statistics (Postgres, Redis) |

## Metrics

Prometheus metrics available at `GET /metrics`:
- `http_requests_total` - Total HTTP requests (method, endpoint, status)
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Current in-flight requests

## Project Structure

```
app/
├── main.py                    # FastAPI app factory
├── pkg/                       # Shared packages
│   ├── client/                # HTTP client (httpx-based)
│   ├── connectors/            # Database/cache connectors (Postgres, Redis)
│   ├── configuration/         # Dishka DI providers
│   ├── logger/                # Logging utilities
│   ├── models/                # Base models & exceptions
│   └── settings/              # Pydantic settings
└── internal/                  # Application code
    ├── models/                # Request/Response schemas
    ├── repository/            # Data access layer
    ├── routes/                # API endpoints
    ├── service/               # Business logic
    └── pkg/middlewares/       # HTTP middlewares
```

## Configuration

Environment variables (prefix with section name, e.g., `POSTGRES__HOST`):

### API Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `API__HOST` | `0.0.0.0` | Server bind host |
| `API__PORT` | `8000` | Server port |
| `API__WORKERS` | `1` | Number of workers |
| `API__DEBUG` | `false` | Enable debug mode (enables /docs) |
| `API__REQUEST_TIMEOUT` | `30` | Request timeout in seconds |
| `API__GRACEFUL_SHUTDOWN_TIMEOUT` | `30` | Max seconds to wait for connector shutdown on exit; gunicorn `--graceful-timeout` should be ≥ this value |

### PostgreSQL Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES__HOST` | required | Database host |
| `POSTGRES__PORT` | required | Database port |
| `POSTGRES__USER` | required | Database user |
| `POSTGRES__PASSWORD` | required | Database password |
| `POSTGRES__DATABASE_NAME` | required | Database name |
| `POSTGRES__MIN_CONNECTION` | `2` | Minimum pool size (per worker) |
| `POSTGRES__MAX_CONNECTION` | `20` | Maximum pool size (per worker); total = workers × this value |
| `POSTGRES__STATEMENT_TIMEOUT` | `30000` | Query timeout (ms) |

### Redis Settings (optional)
| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS__ENABLED` | `false` | Enable Redis connector |
| `REDIS__URL` | `redis://localhost:6379/0` | Redis URL; path segment is logical DB index (e.g. `/0`, `/1`, 0–15) |
| `REDIS__SOCKET_TIMEOUT` | `5.0` | Socket timeout (s) |
| `REDIS__MAX_CONNECTIONS` | `10` | Max connections in pool (per worker) |

## Migrations

```bash
make migrate          # Apply migrations
make migrate-rollback # Rollback all
make migrate-reload   # Rollback and reapply
make migrate-list     # List migration status
```

Migrations are stored in `migrations/` directory.

## Development

```bash
make fmt     # Format code (autoflake, isort, black, docformatter)
make check   # Run linters (flake8, bandit, safety)
make mypy    # Type checking
make clean   # Remove __pycache__
```

## Adding New Features

### 1. Add a new route
```python
# app/internal/routes/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_users():
    return []
```

### 2. Register in routes/__init__.py
```python
from app.internal.routes.users import router as users_router
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
```

### 3. Add repository to DI
```python
# app/configuration/providers/repository.py
@provide(scope=Scope.REQUEST)
def user_repository(self, connector: PostgresConnector) -> UserRepository:
    return UserRepository(connector)
```
