__all__ = ["TokenFields"]

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.pkg.models.base import BaseModel


class BaseToken(BaseModel):
    """Базовая модель для всех моделей токена."""


class TokenFields:
    jti = Annotated[str, Field(description="JWT ID — уникальный идентификатор токена")]
    user_id = Annotated[UUID, Field(description="ID пользователя")]
    access_token = Annotated[str, Field(description="JWT access token")]
    refresh_token = Annotated[str, Field(description="JWT refresh token")]
    token_type = Annotated[str, Field(default="bearer", description="Тип токена")]
    expires_at = Annotated[datetime, Field(description="Дата и время истечения токена")]
    revoked = Annotated[bool, Field(default=False, description="Отозван ли токен")]
    created_at = Annotated[datetime, Field(description="Дата и время создания токена")]

