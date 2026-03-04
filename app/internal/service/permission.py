"""Сервис для работы с разрешениями (permissions)."""

from uuid import UUID

from app.internal.models.permissions import api, repo
from app.internal.repository.postgres.permission import PermissionRepo
from app.pkg.models.base import ConflictError, NotFoundError


class PermissionService:
    """Бизнес-логика для управления разрешениями."""

    def __init__(self, permission_repo: PermissionRepo):
        self._repo = permission_repo

    async def create(
        self, request: api.CreatePermissionAPIRequest
    ) -> api.PermissionAPIResponse:
        """Создать новое разрешение. Raises ConflictError если code уже существует."""
        existing = await self._repo.read_by_code(
            repo.ReadPermissionByCodeRepoQuery(code=request.code)
        )
        if existing:
            raise ConflictError(
                message="Разрешение с таким кодом уже существует",
                details={"code": request.code},
            )
        permission = await self._repo.create(
            request.migrate(repo.CreatePermissionRepoCommand)
        )
        return permission.migrate(api.PermissionAPIResponse)

    async def read_by_code(self, code: str) -> api.PermissionAPIResponse:
        """Получить разрешение по коду. Raises NotFoundError если не найдено."""
        permission = await self._repo.read_by_code(
            repo.ReadPermissionByCodeRepoQuery(code=code)
        )
        if not permission:
            raise NotFoundError(
                message="Разрешение не найдено",
                details={"code": code},
            )
        return permission.migrate(api.PermissionAPIResponse)

    async def list_all(self) -> list[api.PermissionAPIResponse]:
        """Получить список всех разрешений."""
        permissions = await self._repo.list_all()
        return [p.migrate(api.PermissionAPIResponse) for p in permissions]

    async def assign_to_user(self, code: str, user_id: UUID) -> None:
        """Назначить разрешение пользователю по коду."""
        permission = await self._repo.read_by_code(
            repo.ReadPermissionByCodeRepoQuery(code=code)
        )
        if not permission:
            raise NotFoundError(
                message="Разрешение не найдено",
                details={"code": code},
            )
        await self._repo.assign_to_user(
            repo.AssignPermissionRepoCommand(user_id=user_id, permission_id=permission.id)
        )

    async def revoke_from_user(self, code: str, user_id: UUID) -> None:
        """Отозвать разрешение у пользователя по коду."""
        permission = await self._repo.read_by_code(
            repo.ReadPermissionByCodeRepoQuery(code=code)
        )
        if not permission:
            raise NotFoundError(
                message="Разрешение не найдено",
                details={"code": code},
            )
        await self._repo.revoke_from_user(
            repo.RevokePermissionRepoCommand(user_id=user_id, permission_id=permission.id)
        )

    async def get_user_permissions(self, user_id: UUID) -> api.UserPermissionsAPIResponse:
        """Получить все разрешения пользователя."""
        permissions = await self._repo.get_user_permissions(
            repo.ReadUserPermissionsRepoQuery(user_id=user_id)
        )
        return api.UserPermissionsAPIResponse(
            user_id=user_id,
            permissions=[p.migrate(api.PermissionAPIResponse) for p in permissions],
        )

    async def has_permission(self, user_id: UUID, code: str) -> bool:
        """Проверить, имеет ли пользователь указанное активное разрешение."""
        return await self._repo.user_has_permission(user_id=user_id, code=code)

