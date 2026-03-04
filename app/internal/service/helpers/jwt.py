"""Утилиты для создания и верификации JWT токенов."""

__all__ = ["create_access_token", "create_refresh_token", "decode_token"]

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from app.pkg.models.base import UnauthorizedError
from app.pkg.settings.settings import JWTSettings


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(
    user_id: str,
    settings: JWTSettings,
) -> tuple[str, datetime]:
    """Создать access JWT токен.

    Returns:
        (encoded_token, expires_at)
    """
    expires_at = _utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expires_at,
        "iat": _utcnow(),
        "jti": str(uuid4()),
    }
    token = jwt.encode(
        payload,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )
    return token, expires_at


def create_refresh_token(
    user_id: str,
    settings: JWTSettings,
) -> tuple[str, str, datetime]:
    """Создать refresh JWT токен.

    Returns:
        (encoded_token, jti, expires_at)
    """
    jti = str(uuid4())
    expires_at = _utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expires_at,
        "iat": _utcnow(),
        "jti": jti,
    }
    token = jwt.encode(
        payload,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )
    return token, jti, expires_at


def decode_token(token: str, settings: JWTSettings) -> dict:
    """Декодировать и верифицировать JWT токен.

    Returns:
        Payload словарь.

    Raises:
        UnauthorizedError: если токен невалидный или истёк.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError(message="Токен истёк")
    except jwt.InvalidTokenError as e:
        raise UnauthorizedError(message=f"Невалидный токен: {e}")

