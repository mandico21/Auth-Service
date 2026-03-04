"""Prometheus метрики для пулов соединений (Postgres, Redis).

Экспортирует gauge-метрики, которые обновляются на каждый scrape через callback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from prometheus_client import Gauge

if TYPE_CHECKING:
    from app.pkg.connectors.postgres import PostgresConnector
    from app.pkg.connectors.redis import RedisConnector

__all__ = ["setup_pool_metrics"]

# ── PostgreSQL pool gauges ─────────────────────────────────────────────────

PG_POOL_SIZE = Gauge(
    "pg_pool_size",
    "Текущий размер пула соединений PostgreSQL",
)

PG_POOL_AVAILABLE = Gauge(
    "pg_pool_available",
    "Доступных соединений в пуле PostgreSQL",
)

PG_POOL_WAITING = Gauge(
    "pg_pool_waiting",
    "Запросов ожидающих соединение из пула PostgreSQL",
)

# ── Redis pool gauges ──────────────────────────────────────────────────────

REDIS_POOL_CREATED = Gauge(
    "redis_pool_created",
    "Создано соединений в пуле Redis",
)

REDIS_POOL_AVAILABLE = Gauge(
    "redis_pool_available",
    "Доступных соединений в пуле Redis",
)

REDIS_POOL_IN_USE = Gauge(
    "redis_pool_in_use",
    "Используемых соединений в пуле Redis",
)


def update_pool_metrics(
    postgres: PostgresConnector | None = None,
    redis: RedisConnector | None = None,
) -> None:
    """Обновить значения gauge-метрик на основе текущих pool stats."""
    if postgres:
        stats = postgres.pool_stats
        if "size" in stats:
            PG_POOL_SIZE.set(stats["size"])
            PG_POOL_AVAILABLE.set(stats["available"])
            PG_POOL_WAITING.set(stats["waiting"])

    if redis:
        stats = redis.pool_stats
        if "created" in stats:
            REDIS_POOL_CREATED.set(stats["created"])
            REDIS_POOL_AVAILABLE.set(stats["available"])
            REDIS_POOL_IN_USE.set(stats["in_use"])


def setup_pool_metrics(
    postgres: PostgresConnector | None = None,
    redis: RedisConnector | None = None,
) -> None:
    """
    Инициализация pool metrics.

    Вызывается один раз при старте приложения (в lifespan).
    Метрики обновляются через /metrics endpoint middleware callback.
    """
    update_pool_metrics(postgres, redis)

