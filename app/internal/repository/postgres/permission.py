"""Репозиторий для работы с разрешениями (permissions)."""

from app.internal.models.permissions import repo
from app.internal.repository import BaseRepository
from app.internal.repository.postgres.handlers import collect_response
from app.pkg.logger import get_logger

logger = get_logger(__name__)


class PermissionRepo(BaseRepository):
    """Репозиторий для операций с разрешениями и привязкой к пользователям."""

    @property
    def table_name(self) -> str:
        return "permissions"

    @collect_response
    async def create(
        self, cmd: repo.CreatePermissionRepoCommand
    ) -> repo.PermissionRepoResponse | None:
        """Создать новое разрешение."""
        sql = """
              INSERT INTO permissions (name, code, description, is_active)
              VALUES (%(name)s, %(code)s, %(description)s, %(is_active)s)
              RETURNING id, name, code, description, is_active, created_at, updated_at \
              """
        return await self.fetch_one(sql, cmd.to_dict())

    @collect_response
    async def read_by_id(
        self, query: repo.ReadPermissionByIdRepoQuery
    ) -> repo.PermissionRepoResponse | None:
        """Получить разрешение по ID."""
        sql = """
              SELECT id, name, code, description, is_active, created_at, updated_at
              FROM permissions
              WHERE id = %(id)s \
              """
        return await self.fetch_one(sql, query.to_dict())

    @collect_response
    async def read_by_code(
        self, query: repo.ReadPermissionByCodeRepoQuery
    ) -> repo.PermissionRepoResponse | None:
        """Получить разрешение по коду."""
        sql = """
              SELECT id, name, code, description, is_active, created_at, updated_at
              FROM permissions
              WHERE code = %(code)s \
              """
        return await self.fetch_one(sql, query.to_dict())

    @collect_response
    async def list_all(self) -> list[repo.PermissionRepoResponse]:
        """Получить все разрешения."""
        sql = """
              SELECT id, name, code, description, is_active, created_at, updated_at
              FROM permissions
              ORDER BY id \
              """
        return await self.fetch_all(sql)

    async def assign_to_user(self, cmd: repo.AssignPermissionRepoCommand) -> None:
        """Назначить разрешение пользователю. При повторном назначении — игнорировать."""
        sql = """
              INSERT INTO user_permissions (user_id, permission_id)
              VALUES (%(user_id)s, %(permission_id)s)
              ON CONFLICT DO NOTHING \
              """
        await self.execute(sql, cmd.to_dict())

    async def revoke_from_user(self, cmd: repo.RevokePermissionRepoCommand) -> None:
        """Отозвать разрешение у пользователя."""
        sql = """
              DELETE FROM user_permissions
              WHERE user_id = %(user_id)s AND permission_id = %(permission_id)s \
              """
        await self.execute(sql, cmd.to_dict())

    @collect_response
    async def get_user_permissions(
        self, query: repo.ReadUserPermissionsRepoQuery
    ) -> list[repo.PermissionRepoResponse]:
        """Получить все разрешения пользователя."""
        sql = """
              SELECT p.id, p.name, p.code, p.description, p.is_active, p.created_at, p.updated_at
              FROM permissions p
              JOIN user_permissions up ON p.id = up.permission_id
              WHERE up.user_id = %(user_id)s
              ORDER BY p.id \
              """
        return await self.fetch_all(sql, query.to_dict())

    async def user_has_permission(self, user_id, code: str) -> bool:
        """Проверить, есть ли у пользователя активное разрешение с данным кодом."""
        sql = """
              SELECT EXISTS (
                  SELECT 1
                  FROM user_permissions up
                  JOIN permissions p ON p.id = up.permission_id
                  WHERE up.user_id = %(user_id)s
                    AND p.code = %(code)s
                    AND p.is_active = TRUE
              ) \
              """
        result = await self.fetch_val(sql, {"user_id": str(user_id), "code": code})
        return bool(result)

