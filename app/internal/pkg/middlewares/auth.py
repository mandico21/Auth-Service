"""FastAPI dependency для проверки JWT access token и получения текущего пользователя."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer

from app.internal.service.helpers.jwt import decode_token
from app.pkg.models.base import UnauthorizedError
from app.pkg.settings import get_settings

# OAuth2 схема — Swagger показывает форму username/password и сам получает токен
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

# Bearer схема — Swagger показывает поле для вставки готового токена вручную
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    oauth2_token: Annotated[str | None, Depends(_oauth2_scheme)],
    bearer_creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> UUID:
    """
    FastAPI Dependency: извлекает и верифицирует Bearer access token.
    Принимает токен из двух источников (любой из двух):
      - OAuth2 Password flow (кнопка Authorize → username/password в Swagger)
      - Прямой Bearer заголовок (Authorization: Bearer <token>)

    Returns:
        UUID пользователя из токена.

    Raises:
        UnauthorizedError: если токен отсутствует, невалидный или истёк.
    """
    token = oauth2_token or (bearer_creds.credentials if bearer_creds else None)

    if not token:
        raise UnauthorizedError(message="Отсутствует токен авторизации")

    jwt_settings = get_settings().JWT
    payload = decode_token(token, jwt_settings)

    if payload.get("type") != "access":
        raise UnauthorizedError(message="Ожидался access token")

    sub = payload.get("sub")
    if not sub:
        raise UnauthorizedError(message="Невалидный payload токена")

    try:
        return UUID(sub)
    except ValueError:
        raise UnauthorizedError(message="Невалидный user_id в токене")


# Удобный алиас для использования в роутерах
CurrentUserID = Annotated[UUID, Depends(get_current_user_id)]
