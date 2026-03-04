__all__ = ["UserFields", "BaseUser"]

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.pkg.models.base import BaseModel


class BaseUser(BaseModel):
    """Базовая модель для всех моделей пользователя."""


class UserFields:
    id = Annotated[UUID, Field(description="ID пользователя")]
    name = Annotated[UUID, Field(description="ID пользователя")]
    first_name = Annotated[str, Field(
        description="Имя пользователя", max_length=50, examples=["Иван"]
    )]
    last_name = Annotated[str, Field(
        description="Фамилия пользователя", max_length=50, examples=["Иванов"]
    )]
    username = Annotated[str, Field(
        description="Имя пользователя для входа в систему", max_length=50, examples=["ivan_ivanov"]
    )]
    email = Annotated[str, Field(
        description="Email пользователя", max_length=100, examples=["example@gmail.com"]
    )]
    password = Annotated[str, Field(
        description="Пароль пользователя", min_length=8, max_length=100
    )]

    is_active = Annotated[bool, Field(description="Активен ли пользователь", examples=[True])]
    is_superuser = Annotated[bool, Field(
        description="Является ли пользователь суперпользователем", examples=[False]
    )]

    created_at = Annotated[datetime, Field(
        description="Дата и время создания пользователя"
    )]
    updated_at = Annotated[datetime, Field(
        description="Дата и время последнего обновления пользователя"
    )]
