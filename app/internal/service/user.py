"""Сервис пользователей — бизнес-логика между роутами и репозиторием."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.internal.models.user.api import CreateUserRequest, UpdateUserRequest
from app.internal.repository.postgres import UserRepository
from app.pkg.logger import get_logger
from app.pkg.models.base import ConflictError, NotFoundError

__all__ = ["UserService"]

logger = get_logger(__name__)


class UserService:
    """
    Сервис пользователей.

    Содержит бизнес-логику:
    - Валидация уникальности email перед созданием
    - Проверка существования перед обновлением/удалением
    - Нормализация данных
    - Логирование бизнес-операций
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._repo = user_repo

    async def get_by_id(self, user_id: UUID) -> dict:
        """
        Получить пользователя по ID.

        Raises:
            NotFoundError: если пользователь не найден
        """
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(
                message="Пользователь не найден",
                details={"user_id": str(user_id)},
            )
        return user

    async def create(self, data: CreateUserRequest) -> dict:
        """
        Создать нового пользователя.

        Бизнес-логика:
        - Нормализация email (lowercase, strip)
        - Проверка уникальности email
        - Создание записи

        Raises:
            ConflictError: если email уже существует
        """
        email = data.email.strip().lower()
        name = data.name.strip()

        # Проверка уникальности
        if await self._repo.email_exists(email):
            raise ConflictError(
                message="Пользователь с таким email уже существует",
                details={"email": email},
            )

        user = await self._repo.create(email=email, name=name)
        logger.info("Пользователь создан: id=%s, email=%s", user["id"], email)
        return user

    async def update(self, user_id: UUID, data: UpdateUserRequest) -> dict:
        """
        Обновить пользователя.

        Raises:
            NotFoundError: если пользователь не найден
            ConflictError: если новый email уже занят
        """
        # Проверяем существование
        existing = await self._repo.get_by_id(user_id)
        if not existing:
            raise NotFoundError(
                message="Пользователь не найден",
                details={"user_id": str(user_id)},
            )

        # Собираем изменённые поля
        fields: dict[str, Any] = {}
        if data.name is not None:
            fields["name"] = data.name.strip()
        if data.email is not None:
            email = data.email.strip().lower()
            # Проверяем уникальность если email меняется
            if email != existing["email"]:
                if await self._repo.email_exists(email):
                    raise ConflictError(
                        message="Пользователь с таким email уже существует",
                        details={"email": email},
                    )
                fields["email"] = email

        if not fields:
            return existing

        user = await self._repo.update(user_id, **fields)
        logger.info("Пользователь обновлён: id=%s, fields=%s", user_id, list(fields.keys()))
        return user

    async def delete(self, user_id: UUID) -> None:
        """
        Удалить пользователя.

        Raises:
            NotFoundError: если пользователь не найден
        """
        deleted = await self._repo.delete(user_id)
        if not deleted:
            raise NotFoundError(
                message="Пользователь не найден",
                details={"user_id": str(user_id)},
            )
        logger.info("Пользователь удалён: id=%s", user_id)

    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at DESC",
    ) -> dict[str, Any]:
        """Получить пагинированный список пользователей."""
        return await self._repo.list_paginated(
            page=page,
            page_size=page_size,
            order_by=order_by,
        )

    async def list_cursor(
        self,
        cursor: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Получить список пользователей с cursor-based пагинацией."""
        return await self._repo.list_cursor(cursor=cursor, limit=limit)

