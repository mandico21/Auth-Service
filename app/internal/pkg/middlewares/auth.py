"""FastAPI dependency для проверки JWT access token и получения текущего пользователя."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.internal.service.helpers.jwt import decode_token
from app.pkg.models.base import UnauthorizedError
from app.pkg.settings import get_settings

_bearer = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> UUID:
    """
    FastAPI Dependency: извлекает и верифицирует Bearer access token из заголовка Authorization.
    Returns:
        UUID пользователя из токена.

    Raises:
        UnauthorizedError: если токен отсутствует, невалидный или истёк.
    """
    if not credentials:
        raise UnauthorizedError(message="Отсутствует токен авторизации")

    jwt_settings = get_settings().JWT
    payload = decode_token(credentials.credentials, jwt_settings)

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
