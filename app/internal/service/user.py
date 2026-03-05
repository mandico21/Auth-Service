from uuid import UUID

from app.internal.models.user import api, repo
from app.internal.repository.postgres import UserRepo
from app.internal.service.helpers import hash_password, verify_password
from app.internal.service.permission import PermissionChecker
from app.pkg.models.base import NotFoundError, ConflictError, UnauthorizedError, ForbiddenError


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

    async def get_me(self, user_id: UUID) -> api.MeAPIResponse:
        """Получить полный профиль текущего пользователя с его permissions."""
        user = await self._repo.read_by_id(
            query=repo.ReadUserByIdRepoQuery(id=user_id)
        )
        if not user:
            raise NotFoundError(message="Пользователь не найден")

        permissions = await self._perm.get_user_permissions(user_id)

        return api.MeAPIResponse(
            **user.to_dict(),
            permissions=permissions,
        )

    async def delete(self, user_id: UUID, actor_id: UUID) -> None:
        """Удалить пользователя. Требует права delete_user."""
        await self._perm.require(actor_id, "delete_user")

    # ── Смена пароля ────────────────────────────────────────────────────────

    async def change_password(
        self,
        user_id: UUID,
        request: api.ChangePasswordAPIRequest,
    ) -> None:
        """Сменить пароль текущего пользователя.

        Проверяет текущий пароль перед заменой.

        Raises:
            UnauthorizedError: если текущий пароль неверный.
            NotFoundError: если пользователь не найден.
        """
        user = await self._repo.read_by_id(
            query=repo.ReadUserByIdRepoQuery(id=user_id)
        )
        if not user:
            raise NotFoundError(message="Пользователь не найден")

        # Нужен хеш — читаем через специальный метод
        user_with_pwd = await self._repo.read_by_username_with_password(
            query=repo.ReadUserByUsernameRepoQuery(username=user.username)
        )
        if not user_with_pwd or not verify_password(user_with_pwd.password, request.current_password):
            raise UnauthorizedError(message="Текущий пароль указан неверно")

        new_hash = hash_password(request.new_password)
        await self._repo.update_password(
            cmd=repo.UpdatePasswordRepoCommand(id=user_id, password=new_hash)
        )

    # ── Сброс пароля (admin) ─────────────────────────────────────────────────

    async def reset_password(
        self,
        target_user_id: UUID,
        actor_id: UUID,
        request: api.ResetPasswordAPIRequest,
    ) -> None:
        """Принудительно сбросить пароль пользователя.

        Только для пользователей с правом ``manage_users``.

        Raises:
            ForbiddenError: если актор не имеет нужного разрешения.
            NotFoundError: если целевой пользователь не найден.
        """
        await self._perm.require(actor_id, "manage_users")

        user = await self._repo.read_by_id(
            query=repo.ReadUserByIdRepoQuery(id=target_user_id)
        )
        if not user:
            raise NotFoundError(message="Пользователь не найден")

        new_hash = hash_password(request.new_password)
        await self._repo.update_password(
            cmd=repo.UpdatePasswordRepoCommand(id=target_user_id, password=new_hash)
        )

    # ── Обновление профиля ───────────────────────────────────────────────────

    async def update_profile(
        self,
        user_id: UUID,
        request: api.UpdateProfileAPIRequest,
    ) -> api.UpdateProfileAPIResponse:
        """Обновить профиль текущего пользователя (имя, фамилия, email).

        Raises:
            NotFoundError: если пользователь не найден.
            ConflictError: если новый email уже занят другим пользователем.
        """
        if request.email:
            existing = await self._repo.read_by_email(
                query=repo.ReadUserByEmailRepoQuery(email=request.email)
            )
            if existing and existing.id != user_id:
                raise ConflictError(
                    message="Пользователь с таким email уже существует",
                    details={"email": request.email},
                )

        updated = await self._repo.update_profile(
            cmd=repo.UpdateProfileRepoCommand(
                id=user_id,
                first_name=request.first_name,
                last_name=request.last_name,
                email=request.email,
            )
        )
        if not updated:
            raise NotFoundError(message="Пользователь не найден")

        return updated.migrate(api.UpdateProfileAPIResponse)

    # ── Управление статусом (admin) ──────────────────────────────────────────

    async def set_active_status(
        self,
        target_user_id: UUID,
        actor_id: UUID,
        request: api.UpdateUserStatusAPIRequest,
    ) -> api.UpdateProfileAPIResponse:
        """Активировать или деактивировать учётную запись пользователя.

        Только для пользователей с правом ``manage_users``.

        Raises:
            ForbiddenError: если актор не имеет нужного разрешения.
            NotFoundError: если целевой пользователь не найден.
        """
        await self._perm.require(actor_id, "manage_users")

        updated = await self._repo.update_status(
            cmd=repo.UpdateUserStatusRepoCommand(
                id=target_user_id,
                is_active=request.is_active,
            )
        )
        if not updated:
            raise NotFoundError(message="Пользователь не найден")

        return updated.migrate(api.UpdateProfileAPIResponse)


