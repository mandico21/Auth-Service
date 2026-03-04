__all__ = [
    "CreateUserRepoCommand",
    "ReadUserByIdRepoQuery",
    "ReadUserByUsernameRepoQuery",
    "ReadUserByEmailRepoQuery",
    "UserRepoResponse",
    "UserWithPasswordRepoResponse",
]

from datetime import datetime
from uuid import UUID

from app.internal.models.user import UserFields, BaseUser
from app.pkg.models.base import BaseModel


class UserResponse(BaseModel):
    """Модель ответа для пользователя."""

    id: UUID
    email: str
    name: str
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    """Модель ответа для списка пользователей с пагинацией."""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    pages: int


# COMMAND
class CreateUserRepoCommand(BaseUser):
    """Команда для создания пользователя."""

    first_name: UserFields.first_name
    last_name: UserFields.last_name
    username: UserFields.username
    email: UserFields.email
    password: UserFields.password


# QUERY
class ReadUserByIdRepoQuery(BaseModel):
    """Запрос для получения пользователя по ID."""

    id: UserFields.id


class ReadUserByUsernameRepoQuery(BaseUser):
    """Запрос для получения пользователя по имени пользователя."""

    username: UserFields.username


class ReadUserByEmailRepoQuery(BaseModel):
    """Модель ответа для запроса получения пользователя по имени пользователя."""

    email: UserFields.email


# RESPONSE
class UserRepoResponse(BaseUser):
    """Модель ответа для репозитория пользователя."""

    id: UserFields.id
    first_name: UserFields.first_name
    last_name: UserFields.last_name
    username: UserFields.username
    email: UserFields.email
    is_active: UserFields.is_active
    is_superuser: UserFields.is_superuser
    created_at: UserFields.created_at
    updated_at: UserFields.updated_at


class UserWithPasswordRepoResponse(BaseUser):
    """Модель ответа для репозитория с хешем пароля (только для аутентификации)."""

    id: UserFields.id
    first_name: UserFields.first_name
    last_name: UserFields.last_name
    username: UserFields.username
    email: UserFields.email
    password: UserFields.password
    created_at: UserFields.created_at
    updated_at: UserFields.updated_at

