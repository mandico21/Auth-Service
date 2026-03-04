from uuid import UUID

from app.internal.models.user import api, repo
from app.internal.repository.postgres import UserRepo
from app.internal.service.helpers import hash_password, verify_password
from app.internal.service.permission import PermissionChecker
from app.pkg.models.base import NotFoundError, ConflictError, UnauthorizedError


class UserService:

    def __init__(self, user_repo: UserRepo, perm: PermissionChecker):
        self._repo = user_repo
        self._perm = perm

    async def authenticate(self, username: str, password: str) -> api.UserAPIResponse:
        """Проверить учётные данные и вернуть пользователя.

        Raises:
            UnauthorizedError: если пользователь не найден или пароль неверный.
        """
        user = await self._repo.read_by_username_with_password(
            query=repo.ReadUserByUsernameRepoQuery(username=username)
        )
        if not user or not verify_password(user.password, password):
            raise UnauthorizedError(message="Неверное имя пользователя или пароль")
        return user.migrate(api.UserAPIResponse)

    async def read_by_username(
        self,
        request: api.ReadUserByUsernameAPIRequest
    ) -> api.UserAPIResponse | None:
        user = await self._repo.read_by_username(
            query=request.migrate(repo.ReadUserByUsernameRepoQuery)
        )
        if not user:
            raise NotFoundError(
                message="Пользователь с таким именем не найден",
                details={"username": request.username},
            )
        return user.migrate(api.UserAPIResponse)

    async def create(self, request: api.CreateUserAPIRequest) -> api.CreateUserAPIResponse:
        check_user = await self._repo.read_by_username(
            query=request.migrate(repo.ReadUserByUsernameRepoQuery)
        )
        if check_user:
            raise ConflictError(
                message="Пользователь с таким именем уже существует",
                details={"username": request.username},
            )

        check_user = await self._repo.read_by_email(
            query=request.migrate(repo.ReadUserByEmailRepoQuery)
        )
        if check_user:
            raise ConflictError(
                message="Пользователь с таким email уже существует",
                details={"email": request.email},
            )

        request.password = hash_password(request.password)
        user = await self._repo.create(request.migrate(repo.CreateUserRepoCommand))
        return user.migrate(api.CreateUserAPIResponse)

    async def delete(self, user_id: UUID, actor_id: UUID) -> None:
        """Удалить пользователя. Требует права delete_user."""
        await self._perm.require(actor_id, "delete_user")
