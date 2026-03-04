"""Провайдер репозиториев для DI контейнера."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from app.internal.repository.postgres import UserRepository, UserRepo
from app.pkg.connectors.postgres import PostgresConnector


class RepositoryProvider(Provider):
    """Предоставляет экземпляры репозиториев."""
    scope = Scope.REQUEST

    @provide
    def user_repo(self, connector: PostgresConnector) -> UserRepo:
        """Предоставляет UserRepo для скоупа запроса."""
        return UserRepo(connector=connector)
