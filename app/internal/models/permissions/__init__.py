__all__ = ["TokenFields", "PermissionFields"]

from datetime import datetime
from typing import Annotated

from pydantic import Field

from app.internal.models.token import TokenFields
from app.pkg.models.base import BaseModel


class BasePermission(BaseModel):
    """Базовая модель для всех разрешений."""


class PermissionFields:
    """Константы для полей разрешений."""

    id = Annotated[int, Field(description="Уникальный идентификатор разрешения", examples=[1])]
    name = Annotated[str, Field(
        description="Уникальное имя разрешения, например 'create_user'", examples=["create_user"]
    )]
    code = Annotated[str, Field(
        description="Уникальный код разрешения, например 'create_user'", examples=["create_user"]
    )]
    description = Annotated[str, Field(
        description="Описание разрешения", examples=["Разрешение на создание пользователя"]
    )]

    is_active = Annotated[bool, Field(
        default=True, description="Активно ли разрешение", examples=[True]
    )]

    created_at = Annotated[datetime, Field(
        description="Дата и время создания разрешения", examples=["2024-01-01T12:00:00Z"]
    )]
    updated_at = Annotated[datetime, Field(
        description="Дата и время последнего обновления разрешения",
        examples=["2024-01-02T12:00:00Z"]
    )]
