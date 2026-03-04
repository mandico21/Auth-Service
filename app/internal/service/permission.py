"""Сервис для работы с разрешениями (permissions)."""

from app.internal.models.permissions import api, repo
from app.internal.repository.postgres.permission import PermissionRepo
from app.pkg.models.base import ConflictError, ForbiddenError, NotFoundError
from uuid import UUID


class PermissionChecker:
    """
    Лёгкий объект для проверки прав пользователя.
    Инжектируется в любой сервис, которому нужна проверка прав,
    без зависимости на весь PermissionService.

    Пример использования в другом сервисе:
        class UserService:
            def __init__(self, user_repo: UserRepo, perm: PermissionChecker):
                self._perm = perm

            async def delete(self, cmd: DeleteUserCommand) -> None:
                await self._perm.require(cmd.actor_id, "delete_user")
                ...
    """

    def __init__(self, permission_repo: PermissionRepo):
        self._repo = permission_repo

    async def has(self, user_id: UUID, code: str) -> bool:
        """Вернуть True если пользователь имеет активное разрешение."""
        return await self._repo.user_has_permission(user_id=user_id, code=code)

    async def require(self, user_id: UUID, code: str) -> None:
        """Проверить право. Raises ForbiddenError если нет."""
        if not await self.has(user_id, code):
            raise ForbiddenError(
                message=f"Недостаточно прав: требуется разрешение '{code}'"
            )

    async def get_user_permissions(
        self, user_id: UUID
    ) -> list[api.PermissionAPIResponse]:
        """Получить список активных разрешений пользователя."""
        permissions = await self._repo.get_user_permissions(
            repo.ReadUserPermissionsRepoQuery(user_id=user_id)
        )
        return [p.migrate(api.PermissionAPIResponse) for p in permissions]


class PermissionService:
    """Бизнес-логика для управления разрешениями."""

    def __init__(self, permission_repo: PermissionRepo, checker: PermissionChecker):
        self._repo = permission_repo
        self._checker = checker

    # ── internal ────────────────────────────────────────────────────────────

    async def _get_permission_by_code(self, code: str) -> repo.PermissionRepoResponse:
        """Получить разрешение по коду или бросить NotFoundError."""
        permission = await self._repo.read_by_code(
            repo.ReadPermissionByCodeRepoQuery(code=code)
        )
        if not permission:
            raise NotFoundError(
                message="Разрешение не найдено",
                details={"code": code},
            )
        return permission

    # ── public ──────────────────────────────────────────────────────────────

    async def create(
        self,
        cmd: api.CreatePermissionAPICommand,
    ) -> api.PermissionAPIResponse:
        """Создать новое разрешение. Требует права manage_permissions."""
        await self._checker.require(cmd.actor_id, "manage_permissions")

        existing = await self._repo.read_by_code(
            repo.ReadPermissionByCodeRepoQuery(code=cmd.code)
        )
        if existing:
            raise ConflictError(
                message="Разрешение с таким кодом уже существует",
                details={"code": cmd.code},
            )
        permission = await self._repo.create(
            cmd.migrate(repo.CreatePermissionRepoCommand)
        )
        return permission.migrate(api.PermissionAPIResponse)

    async def read_by_code(self, query: repo.ReadPermissionByCodeRepoQuery) -> api.PermissionAPIResponse:
        """Получить разрешение по коду."""
        permission = await self._get_permission_by_code(query.code)
        return permission.migrate(api.PermissionAPIResponse)

    async def list_all(self) -> list[api.PermissionAPIResponse]:
        """Получить список всех разрешений."""
        permissions = await self._repo.list_all()
        return [p.migrate(api.PermissionAPIResponse) for p in permissions]

    async def assign_to_user(self, cmd: api.AssignPermissionAPICommand) -> None:
        """Назначить разрешение пользователю. Требует права manage_permissions."""
        await self._checker.require(cmd.actor_id, "manage_permissions")

        permission = await self._get_permission_by_code(cmd.code)
        await self._repo.assign_to_user(
            repo.AssignPermissionRepoCommand(user_id=cmd.user_id, permission_id=permission.id)
        )

    async def revoke_from_user(self, cmd: api.RevokePermissionAPICommand) -> None:
        """Отозвать разрешение у пользователя. Требует права manage_permissions."""
        await self._checker.require(cmd.actor_id, "manage_permissions")

        permission = await self._get_permission_by_code(cmd.code)
        await self._repo.revoke_from_user(
            repo.RevokePermissionRepoCommand(user_id=cmd.user_id, permission_id=permission.id)
        )

    async def get_user_permissions(
        self, query: api.GetUserPermissionsAPIQuery
    ) -> api.UserPermissionsAPIResponse:
        """Получить все разрешения пользователя."""
        permissions = await self._repo.get_user_permissions(
            repo.ReadUserPermissionsRepoQuery(user_id=query.user_id)
        )
        return api.UserPermissionsAPIResponse(
            user_id=query.user_id,
            permissions=[p.migrate(api.PermissionAPIResponse) for p in permissions],
        )

    async def has_permission(self, user_id: UUID, code: str) -> bool:
        """Проверить, имеет ли пользователь указанное активное разрешение."""
        return await self._checker.has(user_id, code)
