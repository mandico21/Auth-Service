__all__ = [
    "CreatePermissionRepoCommand",
    "ReadPermissionByIdRepoQuery",
    "ReadPermissionByCodeRepoQuery",
    "AssignPermissionRepoCommand",
    "RevokePermissionRepoCommand",
    "ReadUserPermissionsRepoQuery",
    "PermissionRepoResponse",
]

from uuid import UUID

from app.internal.models.permissions import BasePermission, PermissionFields
from app.pkg.models.base import BaseModel


# COMMAND
class CreatePermissionRepoCommand(BasePermission):
    """Команда для создания разрешения."""

    name: PermissionFields.name
    code: PermissionFields.code
    description: PermissionFields.description
    is_active: PermissionFields.is_active


class AssignPermissionRepoCommand(BaseModel):
    """Команда для назначения разрешения пользователю."""

    user_id: UUID
    permission_id: int


class RevokePermissionRepoCommand(BaseModel):
    """Команда для отзыва разрешения у пользователя."""

    user_id: UUID
    permission_id: int


# QUERY
class ReadPermissionByIdRepoQuery(BaseModel):
    """Запрос для получения разрешения по ID."""

    id: PermissionFields.id


class ReadPermissionByCodeRepoQuery(BaseModel):
    """Запрос для получения разрешения по коду."""

    code: PermissionFields.code


class ReadUserPermissionsRepoQuery(BaseModel):
    """Запрос для получения всех разрешений пользователя."""

    user_id: UUID


# RESPONSE
class PermissionRepoResponse(BasePermission):
    """Ответ репозитория с данными разрешения."""

    id: PermissionFields.id
    name: PermissionFields.name
    code: PermissionFields.code
    description: PermissionFields.description
    is_active: PermissionFields.is_active
    created_at: PermissionFields.created_at
    updated_at: PermissionFields.updated_at

