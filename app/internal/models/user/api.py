__all__ = [
    "CreateUserAPIRequest",
    "CreateUserAPIResponse",
    "ReadUserByUsernameAPIRequest",
    "ReadUserByEmailAPIRequest",
    "UserAPIResponse",
    "MeAPIResponse",
    "ChangePasswordAPIRequest",
    "ResetPasswordAPIRequest",
    "UpdateProfileAPIRequest",
    "UpdateProfileAPIResponse",
    "UpdateUserStatusAPIRequest",
]

from app.internal.models.permissions.api import PermissionAPIResponse
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


class MeAPIResponse(BaseUser):
    """Полный профиль текущего авторизованного пользователя с permissions."""

    id: UserFields.id
    first_name: UserFields.first_name
    last_name: UserFields.last_name
    username: UserFields.username
    email: UserFields.email
    is_active: UserFields.is_active
    is_superuser: UserFields.is_superuser
    permissions: list[PermissionAPIResponse]
    created_at: UserFields.created_at
    updated_at: UserFields.updated_at


# ── Смена / сброс пароля ────────────────────────────────────────────────────

class ChangePasswordAPIRequest(BaseUser):
    """Запрос на смену пароля — текущий и новый пароль."""

    current_password: UserFields.password
    new_password: UserFields.password


class ResetPasswordAPIRequest(BaseUser):
    """Запрос на принудительный сброс пароля (только для администраторов)."""

    new_password: UserFields.password


# ── Обновление профиля ──────────────────────────────────────────────────────

class UpdateProfileAPIRequest(BaseUser):
    """Запрос на обновление профиля: имя и/или email."""

    first_name: UserFields.first_name | None = None
    last_name: UserFields.last_name | None = None
    email: UserFields.email | None = None


class UpdateProfileAPIResponse(BaseUser):
    """Ответ после успешного обновления профиля."""

    id: UserFields.id
    first_name: UserFields.first_name
    last_name: UserFields.last_name
    username: UserFields.username
    email: UserFields.email
    is_active: UserFields.is_active
    is_superuser: UserFields.is_superuser
    created_at: UserFields.created_at
    updated_at: UserFields.updated_at


# ── Управление статусом ─────────────────────────────────────────────────────

class UpdateUserStatusAPIRequest(BaseUser):
    """Запрос на изменение статуса пользователя (activate / deactivate)."""

    is_active: UserFields.is_active

