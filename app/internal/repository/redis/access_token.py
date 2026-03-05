"""Репозиторий access токенов для Redis.

Хранит два вида записей:
  - Активные jti:  access_token:<jti>  = <user_id>   (TTL = время жизни токена)
  - Blocklist:     access_blocklist:<jti> = "1"        (TTL = оставшееся время жизни токена)
"""

from __future__ import annotations

from app.pkg.connectors.redis import RedisConnector
from app.pkg.logger import get_logger

logger = get_logger(__name__)

_ACTIVE_PREFIX = "access_token:"
_BLOCK_PREFIX = "access_blocklist:"


class AccessTokenRedisRepo:
    """Управляет активными access-токенами и их блокировкой в Redis."""

    def __init__(self, connector: RedisConnector) -> None:
        self._connector = connector

    # ── Активные токены ──────────────────────────────────────────────────────

    async def save(self, jti: str, user_id: str, ttl_seconds: int) -> None:
        """Зарегистрировать выданный access-токен."""
        async with self._connector.connect() as client:
            await client.set(f"{_ACTIVE_PREFIX}{jti}", user_id, ex=ttl_seconds)

    async def get_user_id(self, jti: str) -> str | None:
        """Получить user_id по jti активного токена."""
        async with self._connector.connect() as client:
            return await client.get(f"{_ACTIVE_PREFIX}{jti}")

    # ── Blocklist ────────────────────────────────────────────────────────────

    async def block(self, jti: str, ttl_seconds: int) -> None:
        """Добавить jti в blocklist на оставшееся время жизни токена."""
        async with self._connector.connect() as client:
            await client.set(f"{_BLOCK_PREFIX}{jti}", "1", ex=ttl_seconds)

    async def is_blocked(self, jti: str) -> bool:
        """Проверить, заблокирован ли токен."""
        async with self._connector.connect() as client:
            return bool(await client.exists(f"{_BLOCK_PREFIX}{jti}"))

    # ── Сброс всех сессий ────────────────────────────────────────────────────

    async def block_all_for_user(self, user_id: str) -> None:
        """Заблокировать все активные access-токены пользователя.

        Находит все ключи ``access_token:<jti>`` с значением == user_id,
        удаляет их и переносит jti в blocklist с тем же TTL.
        """
        async with self._connector.connect() as client:
            async for key in client.scan_iter(f"{_ACTIVE_PREFIX}*"):
                value = await client.get(key)
                if value != user_id:
                    continue
                ttl = await client.ttl(key)
                jti = key.removeprefix(_ACTIVE_PREFIX)
                await client.delete(key)
                if ttl > 0:
                    await client.set(f"{_BLOCK_PREFIX}{jti}", "1", ex=ttl)

