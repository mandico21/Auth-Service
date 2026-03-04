"""Провайдер сервисного слоя для DI контейнера."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from app.internal.repository.postgres import UserRepo, RefreshTokenRepo, PermissionRepo
from app.internal.repository.redis import RefreshTokenRedisRepo
from app.internal.service import UserService
from app.internal.service.token import TokenService
from app.internal.service.permission import PermissionChecker, PermissionService
from app.pkg.settings import Settings


class ServiceProvider(Provider):
    """Предоставляет экземпляры сервисного слоя."""
    scope = Scope.REQUEST

    @provide
    def permission_checker(self, permission_repo: PermissionRepo) -> PermissionChecker:
        """Предоставляет PermissionChecker — используется в любом сервисе."""
        return PermissionChecker(permission_repo=permission_repo)

    @provide
    def user_service(self, user_repo: UserRepo, perm: PermissionChecker) -> UserService:
        """Предоставляет UserService для скоупа запроса."""
        return UserService(user_repo=user_repo, perm=perm)

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

    @provide
    def permission_service(
        self, permission_repo: PermissionRepo, checker: PermissionChecker
    ) -> PermissionService:
        """Предоставляет PermissionService для скоупа запроса."""
        return PermissionService(permission_repo=permission_repo, checker=checker)
