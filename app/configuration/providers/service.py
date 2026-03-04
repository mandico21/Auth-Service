"""Провайдер сервисного слоя для DI контейнера."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from app.internal.repository.postgres import UserRepo
from app.internal.service import UserService


class ServiceProvider(Provider):
    """Предоставляет экземпляры сервисного слоя."""
    scope = Scope.REQUEST

    @provide
    def user_service(self, user_repo: UserRepo) -> UserService:
        """Предоставляет UserService для скоупа запроса."""
        return UserService(user_repo=user_repo)
