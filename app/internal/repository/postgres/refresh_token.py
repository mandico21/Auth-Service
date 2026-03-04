"""Репозиторий refresh токенов для PostgreSQL."""

from app.internal.models.token import repo
from app.internal.repository import BaseRepository
from app.internal.repository.postgres.handlers import collect_response
from app.pkg.logger import get_logger

logger = get_logger(__name__)


class RefreshTokenRepo(BaseRepository):

    @property
    def table_name(self) -> str:
        return "refresh_tokens"

    @collect_response
    async def create(
        self, cmd: repo.CreateRefreshTokenRepoCommand
    ) -> repo.RefreshTokenRepoResponse | None:
        sql = """
              INSERT INTO refresh_tokens (user_id, jti, expires_at)
              VALUES (%(user_id)s, %(jti)s, %(expires_at)s)
              RETURNING id, user_id, jti, expires_at, revoked, created_at
              """
        res = await self.fetch_one(sql, cmd.to_dict())
        return res

    @collect_response
    async def get_by_jti(
        self, query: repo.GetRefreshTokenByJtiRepoQuery
    ) -> repo.RefreshTokenRepoResponse | None:
        sql = """
              SELECT id, user_id, jti, expires_at, revoked, created_at
              FROM refresh_tokens
              WHERE jti = %(jti)s
              """
        res = await self.fetch_one(sql, query.to_dict())
        return res

    @collect_response
    async def revoke(
        self, cmd: repo.RevokeRefreshTokenRepoCommand
    ) -> repo.RefreshTokenRepoResponse | None:
        sql = """
              UPDATE refresh_tokens
              SET revoked = TRUE
              WHERE jti = %(jti)s
              RETURNING id, user_id, jti, expires_at, revoked, created_at
              """
        res = await self.fetch_one(sql, cmd.to_dict())
        return res

    async def revoke_all_for_user(self, user_id: str) -> None:
        """Отозвать все refresh токены пользователя (logout со всех устройств)."""
        sql = """
              UPDATE refresh_tokens
              SET revoked = TRUE
              WHERE user_id = %(user_id)s AND revoked = FALSE
              """
        await self.execute(sql, {"user_id": user_id})

