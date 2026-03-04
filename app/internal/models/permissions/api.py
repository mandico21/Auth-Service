__all__ = [
    "CreatePermissionAPIRequest",
    "PermissionAPIResponse",
    "AssignPermissionAPIRequest",
    "UserPermissionsAPIResponse",
]

from uuid import UUID

from app.internal.models.permissions import BasePermission, PermissionFields
from app.pkg.models.base import BaseModel


# REQUEST
class CreatePermissionAPIRequest(BasePermission):
    """API запрос на создание разрешения."""

    name: PermissionFields.name
    code: PermissionFields.code
    description: PermissionFields.description
    is_active: PermissionFields.is_active


class AssignPermissionAPIRequest(BaseModel):
    """API запрос на назначение/отзыв разрешения у пользователя."""

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

