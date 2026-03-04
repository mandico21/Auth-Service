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
