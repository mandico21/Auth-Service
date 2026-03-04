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
              returning id, username, email, first_name, last_name, created_at, updated_at \
              """
        res = await self.fetch_one(sql, cmd.to_dict())
        return res

    @collect_response
    async def read_by_username(
        self,
        query: repo.ReadUserByUsernameRepoQuery
    ) -> repo.UserRepoResponse | None:
        sql = """
              select id, username, email, first_name, last_name, created_at, updated_at
              from users
              where username = %(username)s \
              """
        res = await self.fetch_one(sql, query.to_dict())
        return res

    @collect_response
    async def read_by_email(
        self,
        query: repo.ReadUserByEmailRepoQuery
    ) -> repo.UserRepoResponse | None:
        sql = """
              select id, username, email, first_name, last_name, created_at, updated_at
              from users
              where email = %(email)s \
              """
        res = await self.fetch_one(sql, query.to_dict())
        return res
