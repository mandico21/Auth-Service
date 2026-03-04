"""Провайдер репозиториев для DI контейнера."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from app.internal.repository.postgres import UserRepo, RefreshTokenRepo
from app.internal.repository.redis import RefreshTokenRedisRepo
from app.pkg.connectors.postgres import PostgresConnector
from app.pkg.connectors.redis import RedisConnector


class RepositoryProvider(Provider):
    """Предоставляет экземпляры репозиториев."""
    scope = Scope.REQUEST

    @provide
    def user_repo(self, connector: PostgresConnector) -> UserRepo:
        """Предоставляет UserRepo для скоупа запроса."""
        return UserRepo(connector=connector)

    @provide
    def refresh_token_repo(self, connector: PostgresConnector) -> RefreshTokenRepo:
        """Предоставляет RefreshTokenRepo (PostgreSQL) для скоупа запроса."""
        return RefreshTokenRepo(connector=connector)

    @provide
    def refresh_token_redis_repo(self, connector: RedisConnector) -> RefreshTokenRedisRepo:
        """Предоставляет RefreshTokenRedisRepo (Redis) для скоупа запроса."""
        return RefreshTokenRedisRepo(connector=connector)

