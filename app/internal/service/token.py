"""Сервис аутентификации и управления токенами."""

from __future__ import annotations

from datetime import datetime, timezone

from app.internal.models.token import api as token_api
from app.internal.models.token import repo as token_repo
from app.internal.repository.postgres import RefreshTokenRepo
from app.internal.repository.redis import RefreshTokenRedisRepo
from app.internal.service.helpers.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.internal.service.user import UserService
from app.pkg.models.base import UnauthorizedError
from app.pkg.settings.settings import JWTSettings


def _ttl_seconds(expires_at: datetime) -> int:
    """Вычислить количество секунд до истечения токена."""
    now = datetime.now(tz=timezone.utc)
    return max(int((expires_at - now).total_seconds()), 1)


class TokenService:
    """Бизнес-логика аутентификации: login, refresh, logout."""

    def __init__(
        self,
        user_service: UserService,
        refresh_token_repo: RefreshTokenRepo,
        refresh_token_redis_repo: RefreshTokenRedisRepo,
        jwt_settings: JWTSettings,
    ) -> None:
        self._user_service = user_service
        self._pg_repo = refresh_token_repo
        self._redis_repo = refresh_token_redis_repo
        self._jwt = jwt_settings

    async def login(self, request: token_api.LoginAPIRequest) -> token_api.TokenAPIResponse:
        """Аутентифицировать пользователя и выдать пару токенов."""
        user = await self._user_service.authenticate(request.username, request.password)

        access_token, _ = create_access_token(str(user.id), self._jwt)
        refresh_token, jti, expires_at = create_refresh_token(str(user.id), self._jwt)

        await self._pg_repo.create(
            token_repo.CreateRefreshTokenRepoCommand(
                user_id=user.id,
                jti=jti,
                expires_at=expires_at,
            )
        )
        await self._redis_repo.save(jti, str(user.id), _ttl_seconds(expires_at))

        return token_api.TokenAPIResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(
        self, request: token_api.RefreshTokenAPIRequest
    ) -> token_api.TokenAPIResponse:
        """Обновить пару токенов по refresh token (Refresh Token Rotation)."""
        payload = decode_token(request.refresh_token, self._jwt)

        if payload.get("type") != "refresh":
            raise UnauthorizedError(message="Ожидался refresh token")

        jti = payload.get("jti")
        user_id = payload.get("sub")

        if not jti or not user_id:
            raise UnauthorizedError(message="Невалидный payload токена")

        if not await self._redis_repo.exists(jti):
            raise UnauthorizedError(message="Токен отозван или истёк")

        # Инвалидируем старый токен (rotation)
        await self._redis_repo.delete(jti)
        await self._pg_repo.revoke(token_repo.RevokeRefreshTokenRepoCommand(jti=jti))

        # Выдаём новую пару
        access_token, _ = create_access_token(user_id, self._jwt)
        new_refresh_token, new_jti, expires_at = create_refresh_token(user_id, self._jwt)

        await self._pg_repo.create(
            token_repo.CreateRefreshTokenRepoCommand(
                user_id=user_id,
                jti=new_jti,
                expires_at=expires_at,
            )
        )
        await self._redis_repo.save(new_jti, user_id, _ttl_seconds(expires_at))

        return token_api.TokenAPIResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )

    async def logout(self, refresh_token: str) -> None:
        """Выход из системы — отзыв refresh token."""
        try:
            payload = decode_token(refresh_token, self._jwt)
        except UnauthorizedError:
            # Токен уже недействителен — logout всё равно успешен
            return

        if payload.get("type") != "refresh":
            raise UnauthorizedError(message="Ожидался refresh token")

        jti = payload.get("jti")
        if not jti:
            return

        await self._redis_repo.delete(jti)
        await self._pg_repo.revoke(token_repo.RevokeRefreshTokenRepoCommand(jti=jti))
