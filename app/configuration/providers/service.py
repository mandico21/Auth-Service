"""Провайдер сервисного слоя для DI контейнера."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from app.internal.repository.postgres import UserRepo, RefreshTokenRepo
from app.internal.repository.redis import RefreshTokenRedisRepo
from app.internal.service import UserService
from app.internal.service.token import TokenService
from app.pkg.settings import Settings


class ServiceProvider(Provider):
    """Предоставляет экземпляры сервисного слоя."""
    scope = Scope.REQUEST

    @provide
    def user_service(self, user_repo: UserRepo) -> UserService:
        """Предоставляет UserService для скоупа запроса."""
        return UserService(user_repo=user_repo)

    @provide
    def token_service(
        self,
        user_service: UserService,
        refresh_token_repo: RefreshTokenRepo,
        refresh_token_redis_repo: RefreshTokenRedisRepo,
        settings: Settings,
    ) -> TokenService:
        """Предоставляет TokenService для скоупа запроса."""
        return TokenService(
            user_service=user_service,
            refresh_token_repo=refresh_token_repo,
            refresh_token_redis_repo=refresh_token_redis_repo,
            jwt_settings=settings.JWT,
        )

