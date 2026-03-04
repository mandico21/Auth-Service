__all__ = [
    "CreatePermissionAPIRequest",
    "CreatePermissionAPICommand",
    "AssignPermissionAPIRequest",
    "AssignPermissionAPICommand",
    "RevokePermissionAPICommand",
    "GetUserPermissionsAPIQuery",
    "PermissionAPIResponse",
    "UserPermissionsAPIResponse",
]

from uuid import UUID

from app.internal.models.permissions import BasePermission, PermissionFields
from app.pkg.models.base import BaseModel


# REQUEST (входящие данные от клиента — только то, что приходит в теле)
class CreatePermissionAPIRequest(BasePermission):
    """Тело запроса на создание разрешения."""

    name: PermissionFields.name
    code: PermissionFields.code
    description: PermissionFields.description
    is_active: PermissionFields.is_active


class AssignPermissionAPIRequest(BaseModel):
    """Тело запроса на назначение/отзыв разрешения."""

    user_id: UUID


# COMMAND (полные команды для сервиса = тело + контекст вызывающего)
class CreatePermissionAPICommand(BasePermission):
    """Команда создания разрешения — тело + actor_id."""

    name: PermissionFields.name
    code: PermissionFields.code
    description: PermissionFields.description
    is_active: PermissionFields.is_active
    actor_id: UUID


class AssignPermissionAPICommand(BaseModel):
    """Команда назначения разрешения пользователю."""

    code: str
    user_id: UUID
    actor_id: UUID


class RevokePermissionAPICommand(BaseModel):
    """Команда отзыва разрешения у пользователя."""

    code: str
    user_id: UUID
    actor_id: UUID


# QUERY
class GetUserPermissionsAPIQuery(BaseModel):
    """Запрос списка разрешений пользователя."""

    user_id: UUID


# RESPONSE
class PermissionAPIResponse(BasePermission):
    """API ответ с данными разрешения."""

    id: PermissionFields.id
    name: PermissionFields.name
    code: PermissionFields.code
    description: PermissionFields.description
    is_active: PermissionFields.is_active
    created_at: PermissionFields.created_at
    updated_at: PermissionFields.updated_at


class UserPermissionsAPIResponse(BaseModel):
    """API ответ со списком разрешений пользователя."""

    user_id: UUID
    permissions: list[PermissionAPIResponse]

