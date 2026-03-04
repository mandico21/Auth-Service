__all__ = [
    "CreateUserAPIRequest",
    "CreateUserAPIResponse",
    "ReadUserByUsernameAPIRequest",
    "ReadUserByEmailAPIRequest",
    "UserAPIResponse",
]

from app.internal.models.user import UserFields, BaseUser
from app.pkg.models.base import BaseModel
from app.pkg.models.types import NotEmptyStr


class CreateUserRequest(BaseModel):
    """Запрос на создание пользователя."""

    email: UserFields.email
    name: UserFields.name


class UpdateUserRequest(BaseModel):
    """Запрос на обновление пользователя."""

    name: NotEmptyStr | None = None
    email: UserFields.email | None = None


# REQUEST
class CreateUserAPIRequest(BaseUser):
    """API модель запроса на создание пользователя."""

    first_name: UserFields.first_name
    last_name: UserFields.last_name
    username: UserFields.username
    email: UserFields.email
    password: UserFields.password


class ReadUserByUsernameAPIRequest(BaseUser):
    """API модель запроса на получение пользователя по имени."""

    username: UserFields.username


class ReadUserByEmailAPIRequest(BaseUser):
    """API модель запроса на получение пользователя по email."""

    email: UserFields.email


# RESPONSE
class CreateUserAPIResponse(BaseUser):
    """API ответ после успешного создания пользователя (без пароля)."""

    id: UserFields.id
    first_name: UserFields.first_name
    last_name: UserFields.last_name
    username: UserFields.username
    email: UserFields.email
    created_at: UserFields.created_at
    updated_at: UserFields.updated_at


class UserAPIResponse(BaseUser):
    """API модель ответа с данными пользователя."""

    id: UserFields.id
    first_name: UserFields.first_name
    last_name: UserFields.last_name
    username: UserFields.username
    email: UserFields.email
    created_at: UserFields.created_at
    updated_at: UserFields.updated_at
