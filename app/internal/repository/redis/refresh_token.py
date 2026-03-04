"""Репозиторий refresh токенов для Redis (быстрая проверка/отзыв по jti)."""

from __future__ import annotations

from app.pkg.connectors.redis import RedisConnector
from app.pkg.logger import get_logger

logger = get_logger(__name__)

_PREFIX = "refresh_token:"


class RefreshTokenRedisRepo:
    """
    Хранит jti refresh-токенов в Redis с TTL.

    Ключ: refresh_token:<jti>
    Значение: строка user_id
    """

    def __init__(self, connector: RedisConnector) -> None:
        self._connector = connector

    async def save(self, jti: str, user_id: str, ttl_seconds: int) -> None:
        """Сохранить jti с TTL (в секундах)."""
        async with self._connector.connect() as client:
            await client.set(f"{_PREFIX}{jti}", user_id, ex=ttl_seconds)

    async def exists(self, jti: str) -> bool:
        """Проверить, существует ли jti (не отозван и не истёк)."""
        async with self._connector.connect() as client:
            result = await client.exists(f"{_PREFIX}{jti}")
            return bool(result)

    async def get_user_id(self, jti: str) -> str | None:
        """Получить user_id по jti."""
        async with self._connector.connect() as client:
            return await client.get(f"{_PREFIX}{jti}")

    async def delete(self, jti: str) -> None:
        """Удалить jti (отзыв токена)."""
        async with self._connector.connect() as client:
            await client.delete(f"{_PREFIX}{jti}")

