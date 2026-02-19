"""Optional Redis connector with connection pool and healthcheck."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import redis.asyncio as redis

from app.pkg.connectors.base import BaseConnector
from app.pkg.settings.settings import RedisSettings

__all__ = ["RedisConnector"]


def _db_from_url(url: str) -> int:
    """Извлечь номер логической базы Redis из URL (путь: /0, /1, …)."""
    try:
        # redis://host:port/N или rediss://user:pass@host:port/N
        parts = url.rstrip("/").rsplit("/", 1)
        if len(parts) == 2:
            return int(parts[1])
    except (ValueError, IndexError):
        pass
    return 0


class RedisConnector(BaseConnector[redis.Redis]):
    """
    Redis connection manager. When ENABLED=False, acts as a no-op:
    healthcheck returns True, connect() raises RuntimeError.

    Номер базы Redis задаётся в URL (например redis://localhost:6379/1 для db 1).
    Один коннектор = один пул = одна логическая база; для нескольких баз — несколько URL/коннекторов.
    """

    def __init__(self, settings: RedisSettings):
        self._settings = settings
        self._client: redis.Redis | None = None
        self._pool: redis.ConnectionPool | None = None
        self._db: int = _db_from_url(settings.URL)

    @property
    def name(self) -> str:
        return "redis"

    @property
    def db(self) -> int:
        """Номер логической базы Redis (из URL)."""
        return self._db

    @property
    def dsn(self) -> str:
        if not self._settings.ENABLED:
            return "redis:disabled"
        # Mask password in URL for logs
        url = self._settings.URL
        if "@" in url and "://" in url:
            scheme, rest = url.split("://", 1)
            if "@" in rest:
                _, host_part = rest.split("@", 1)
                return f"{scheme}://***@{host_part}"
        return url

    async def startup(self) -> None:
        if not self._settings.ENABLED:
            return
        self._pool = redis.ConnectionPool.from_url(
            self._settings.URL,
            max_connections=self._settings.MAX_CONNECTIONS,
            socket_timeout=self._settings.SOCKET_TIMEOUT,
            socket_connect_timeout=self._settings.SOCKET_CONNECT_TIMEOUT,
            decode_responses=self._settings.DECODE_RESPONSES,
        )
        self._client = redis.Redis(connection_pool=self._pool)

    async def shutdown(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        if self._pool is not None:
            await self._pool.aclose()
            self._pool = None

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[redis.Redis]:
        if not self._settings.ENABLED:
            raise RuntimeError("Redis is disabled (REDIS__ENABLED=false)")
        if self._client is None:
            raise RuntimeError("RedisConnector is not started")
        yield self._client

    async def healthcheck(self) -> bool:
        if not self._settings.ENABLED:
            return True
        try:
            if self._client is None:
                return False
            await self._client.ping()
            return True
        except Exception:
            return False

    @property
    def pool_stats(self) -> dict[str, Any]:
        if not self._settings.ENABLED or self._pool is None:
            return {"status": "disabled" if not self._settings.ENABLED else "not_started", "db": self._db}
        fallback = {"status": "ready", "db": self._db, "created": 0, "available": 0, "in_use": 0}
        try:
            created = getattr(self._pool, "_created_connections", 0)
            available = len(getattr(self._pool, "_available_connections", []))
            in_use = len(getattr(self._pool, "_in_use_connections", set()))
            return {
                "status": "ready",
                "db": self._db,
                "created": created,
                "available": available,
                "in_use": in_use,
            }
        except Exception:
            return fallback
