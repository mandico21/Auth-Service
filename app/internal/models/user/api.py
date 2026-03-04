"""Request модели для User API."""
from app.internal.models.user import UserFields
from app.pkg.models.base import BaseModel
from app.pkg.models.types import NotEmptyStr


class CreateUserRequest(BaseModel):
    """Запрос на создание пользователя."""

    email: UserFields.email
    name: UserFields.name


class UpdateUserRequest(BaseModel):
    """Запрос на обновление пользователя."""

    name: NotEmptyStr | None = None
    email: UserFields.Email | None = None
