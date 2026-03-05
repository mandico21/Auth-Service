"""Провайдер репозиториев для DI контейнера."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from app.internal.repository.postgres import UserRepo, RefreshTokenRepo, PermissionRepo
from app.internal.repository.redis import RefreshTokenRedisRepo, AccessTokenRedisRepo
from app.pkg.connectors.postgres import PostgresConnector
from app.pkg.connectors.redis import RedisConnector


class RepositoryProvider(Provider):
    """Предоставляет экземпляры репозиториев."""
    scope = Scope.REQUEST

    @provide
    def user_repo(self, connector: PostgresConnector) -> UserRepo:
        return UserRepo(connector=connector)

    @provide
    def refresh_token_repo(self, connector: PostgresConnector) -> RefreshTokenRepo:
        return RefreshTokenRepo(connector=connector)

    @provide
    def refresh_token_redis_repo(self, connector: RedisConnector) -> RefreshTokenRedisRepo:
        return RefreshTokenRedisRepo(connector=connector)

    @provide
    def access_token_redis_repo(self, connector: RedisConnector) -> AccessTokenRedisRepo:
        """Предоставляет AccessTokenRedisRepo (blocklist access-токенов) для скоупа запроса."""
        return AccessTokenRedisRepo(connector=connector)

    @provide
    def permission_repo(self, connector: PostgresConnector) -> PermissionRepo:
        return PermissionRepo(connector=connector)

