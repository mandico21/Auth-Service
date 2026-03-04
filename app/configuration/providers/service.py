"""Провайдер сервисного слоя для DI контейнера."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from app.internal.repository.postgres import UserRepository
from app.internal.service.user import UserService


class ServiceProvider(Provider):
    """Предоставляет экземпляры сервисного слоя."""

    @provide(scope=Scope.REQUEST)
    def user_service(self, user_repo: UserRepository) -> UserService:
        """Предоставляет UserService для скоупа запроса."""
        return UserService(user_repo)
