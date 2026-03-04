__all__ = ["UserFields"]

from typing import Annotated
from uuid import UUID

from pydantic import Field


class UserFields:
    id = Annotated[UUID, Field(description="ID пользователя")]
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

    created_at = Annotated[str, Field(
        description="Дата и время создания пользователя", examples=["2022-01-01T00:00:00Z"]
    )]
    updated_at = Annotated[str, Field(
        description="Дата и время последнего обновления пользователя",
        examples=["2022-01-01T00:00:00Z"]
    )]
