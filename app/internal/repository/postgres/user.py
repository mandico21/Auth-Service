from app.internal.models.user import repo
from app.internal.repository import BaseRepository
from app.internal.repository.postgres.handlers import collect_response
from app.pkg.logger import get_logger

logger = get_logger(__name__)


class UserRepo(BaseRepository):

    @property
    def table_name(self) -> str:
        return 'users'

    @collect_response
    async def create(self, cmd: repo.CreateUserRepoCommand) -> repo.UserRepoResponse | None:
        sql = """
              insert into users (username, email, first_name, last_name, password)
              values (%(username)s, %(email)s, %(first_name)s, %(last_name)s, %(password)s)
              returning id, username, email, first_name, last_name,
                        is_active, is_superuser, created_at, updated_at \
              """
        return await self.fetch_one(sql, cmd.to_dict())

    @collect_response
    async def read_by_id(
        self,
        query: repo.ReadUserByIdRepoQuery,
    ) -> repo.UserRepoResponse | None:
        """Получить пользователя по UUID."""
        sql = """
              select id, username, email, first_name, last_name,
                     is_active, is_superuser, created_at, updated_at
              from users
              where id = %(id)s \
              """
        return await self.fetch_one(sql, query.to_dict())

    @collect_response
    async def read_by_username(
        self,
        query: repo.ReadUserByUsernameRepoQuery
    ) -> repo.UserRepoResponse | None:
        sql = """
              select id, username, email, first_name, last_name,
                     is_active, is_superuser, created_at, updated_at
              from users
              where username = %(username)s \
              """
        return await self.fetch_one(sql, query.to_dict())

    @collect_response
    async def read_by_username_with_password(
        self,
        query: repo.ReadUserByUsernameRepoQuery
    ) -> repo.UserWithPasswordRepoResponse | None:
        """Получить пользователя вместе с хешем пароля (только для аутентификации)."""
        sql = """
              select id, username, email, first_name, last_name, password, created_at, updated_at
              from users
              where username = %(username)s \
              """
        return await self.fetch_one(sql, query.to_dict())

    @collect_response
    async def read_by_email(
        self,
        query: repo.ReadUserByEmailRepoQuery
    ) -> repo.UserRepoResponse | None:
        sql = """
              select id, username, email, first_name, last_name,
                     is_active, is_superuser, created_at, updated_at
              from users
              where email = %(email)s \
              """
        return await self.fetch_one(sql, query.to_dict())

    @collect_response
    async def update_password(
        self,
        cmd: repo.UpdatePasswordRepoCommand,
    ) -> repo.UserRepoResponse | None:
        """Обновить хеш пароля пользователя."""
        sql = """
              update users
              set password   = %(password)s,
                  updated_at = now()
              where id = %(id)s
              returning id, username, email, first_name, last_name,
                        is_active, is_superuser, created_at, updated_at \
              """
        return await self.fetch_one(sql, cmd.to_dict())

    @collect_response
    async def update_profile(
        self,
        cmd: repo.UpdateProfileRepoCommand,
    ) -> repo.UserRepoResponse | None:
        """Обновить профиль пользователя (first_name, last_name, email)."""
        sql = """
              update users
              set first_name = coalesce(%(first_name)s, first_name),
                  last_name  = coalesce(%(last_name)s,  last_name),
                  email      = coalesce(%(email)s,      email),
                  updated_at = now()
              where id = %(id)s
              returning id, username, email, first_name, last_name,
                        is_active, is_superuser, created_at, updated_at \
              """
        return await self.fetch_one(sql, cmd.to_dict())

    @collect_response
    async def update_status(
        self,
        cmd: repo.UpdateUserStatusRepoCommand,
    ) -> repo.UserRepoResponse | None:
        """Активировать или деактивировать пользователя."""
        sql = """
              update users
              set is_active  = %(is_active)s,
                  updated_at = now()
              where id = %(id)s
              returning id, username, email, first_name, last_name,
                        is_active, is_superuser, created_at, updated_at \
              """
        return await self.fetch_one(sql, cmd.to_dict())

