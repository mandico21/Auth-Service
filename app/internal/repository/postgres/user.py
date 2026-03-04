"""User репозиторий для PostgreSQL."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.internal.repository.base import BaseRepository, with_retry
from app.pkg.connectors.postgres import PostgresConnector


class UserRepository(BaseRepository):
    """Репозиторий для операций с пользователями в БД."""

    def __init__(self, connector: PostgresConnector):
        super().__init__(connector)

    @property
    def table_name(self) -> str:
        return "users"

    @with_retry(max_attempts=3, delay=0.1)
    async def get_by_id(self, user_id: UUID) -> dict | None:
        """Получить пользователя по ID."""
        query = """
            SELECT id, email, name, created_at, updated_at
            FROM users
            WHERE id = %s
        """
        return await self.fetch_one(query, (user_id,))

    @with_retry(max_attempts=3, delay=0.1)
    async def get_by_email(self, email: str) -> dict | None:
        """Получить пользователя по email."""
        query = """
            SELECT id, email, name, created_at, updated_at
            FROM users
            WHERE email = %s
        """
        return await self.fetch_one(query, (email,))

    @with_retry(max_attempts=3, delay=0.1)
    async def create(self, email: str, name: str) -> dict:
        """Создать нового пользователя и вернуть созданную запись."""
        query = """
            INSERT INTO users (email, name)
            VALUES (%s, %s)
            RETURNING id, email, name, created_at, updated_at
        """
        return await self.fetch_one(query, (email, name))

    @with_retry(max_attempts=3, delay=0.1)
    async def create_many(self, users: list[dict[str, str]]) -> int:
        """
        Массовое создание пользователей.

        Аргументы:
            users: Список словарей с полями email и name

        Возвращает:
            Количество созданных пользователей
        """
        return await self.insert_many(users)

    @with_retry(max_attempts=3, delay=0.1)
    async def update(self, user_id: UUID, **fields: Any) -> dict | None:
        """Обновить поля пользователя."""
        if not fields:
            return await self.get_by_id(user_id)

        # Валидация имён полей через whitelist
        allowed_fields = {"email", "name"}
        invalid = set(fields.keys()) - allowed_fields
        if invalid:
            raise ValueError(f"Недопустимые поля для обновления: {invalid}")

        set_clause = ", ".join(f"{self._validate_identifier(k)} = %s" for k in fields.keys())
        query = f"""
            UPDATE users
            SET {set_clause}, updated_at = NOW()
            WHERE id = %s
            RETURNING id, email, name, created_at, updated_at
        """
        params = (*fields.values(), user_id)
        return await self.fetch_one(query, params)

    @with_retry(max_attempts=3, delay=0.1)
    async def delete(self, user_id: UUID) -> bool:
        """Удалить пользователя по ID. Возвращает True если удалён."""
        query = """
            DELETE FROM users
            WHERE id = %s
            RETURNING id
        """
        result = await self.fetch_one(query, (user_id,))
        return result is not None

    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at DESC",
    ) -> list[dict]:
        """
        Получить список пользователей с пагинацией.

        Аргументы:
            limit: Максимальное количество записей
            offset: Смещение от начала
            order_by: Поле и направление сортировки
        """
        # Безопасная валидация order_by (защита от SQL injection)
        allowed_fields = {"created_at", "updated_at", "email", "name"}
        allowed_directions = {"ASC", "DESC"}

        parts = order_by.split()
        if len(parts) == 2:
            field, direction = parts
            if field in allowed_fields and direction.upper() in allowed_directions:
                order_clause = f"{field} {direction.upper()}"
            else:
                order_clause = "created_at DESC"
        else:
            order_clause = "created_at DESC"

        query = f"""
            SELECT id, email, name, created_at, updated_at
            FROM users
            ORDER BY {order_clause}
            LIMIT %s OFFSET %s
        """
        return await self.fetch_all(query, (limit, offset))

    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at DESC",
    ) -> dict[str, Any]:
        """
        Получить пагинированный список пользователей с метаданными.

        Использует оконную функцию COUNT(*) OVER() для получения total
        в одном запросе (1 соединение вместо 2).

        Возвращает:
            {
                "items": [...],
                "total": 150,
                "page": 1,
                "page_size": 50,
                "pages": 3
            }
        """
        # Защита от некорректных значений
        page = max(1, page)
        page_size = min(max(1, page_size), 1000)  # Максимум 1000 записей
        offset = (page - 1) * page_size

        # Безопасная валидация order_by (защита от SQL injection)
        allowed_fields = {"created_at", "updated_at", "email", "name"}
        allowed_directions = {"ASC", "DESC"}

        parts = order_by.split()
        if len(parts) == 2:
            field, direction = parts
            if field in allowed_fields and direction.upper() in allowed_directions:
                order_clause = f"{field} {direction.upper()}"
            else:
                order_clause = "created_at DESC"
        else:
            order_clause = "created_at DESC"

        # Одна оконная функция = 1 соединение из пула вместо 2
        query = f"""
            SELECT id, email, name, created_at, updated_at,
                   COUNT(*) OVER() AS total_count
            FROM users
            ORDER BY {order_clause}
            LIMIT %s OFFSET %s
        """
        rows = await self.fetch_all(query, (page_size, offset))

        total = rows[0]["total_count"] if rows else await self.count()
        # Убираем служебное поле из результатов
        items = [{k: v for k, v in row.items() if k != "total_count"} for row in rows]

        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }

    async def email_exists(self, email: str) -> bool:
        """Проверить существование пользователя с данным email."""
        return await self.exists("email = %s", (email,))

    async def count_by_domain(self, domain: str) -> int:
        """Подсчитать количество пользователей с email в указанном домене."""
        return await self.count(
            "email LIKE %s",
            (f"%@{domain}",),
        )

    async def find_by_name_pattern(self, pattern: str, limit: int = 50) -> list[dict]:
        """
        Найти пользователей по частичному совпадению имени.

        Аргументы:
            pattern: Паттерн для поиска (будет обёрнут в %pattern%)
            limit: Максимальное количество результатов
        """
        query = """
            SELECT id, email, name, created_at, updated_at
            FROM users
            WHERE name ILIKE %s
            ORDER BY name
            LIMIT %s
        """
        return await self.fetch_all(query, (f"%{pattern}%", limit))

    async def bulk_update_domain(self, old_domain: str, new_domain: str) -> int:
        """
        Массовое обновление email домена для пользователей.

        Возвращает:
            Количество обновлённых записей
        """
        query = """
            UPDATE users
            SET email = REPLACE(email, %s, %s),
                updated_at = NOW()
            WHERE email LIKE %s
        """
        async with self.transaction() as conn:
            cursor = await conn.execute(
                query,
                (f"@{old_domain}", f"@{new_domain}", f"%@{old_domain}"),
            )
            return cursor.rowcount

    async def create_with_validation(self, email: str, name: str) -> dict:
        """
        Создать пользователя с валидацией уникальности email.

        Raises:
            ValueError: Если email уже существует
        """
        # Проверка в транзакции для атомарности
        async with self.transaction() as conn:
            # Проверяем существование
            exists = await self.exists("email = %s", (email,), conn)
            if exists:
                raise ValueError(f"Пользователь с email {email} уже существует")

            # Создаём
            query = """
                INSERT INTO users (email, name)
                VALUES (%s, %s)
                RETURNING id, email, name, created_at, updated_at
            """
            result = await conn.execute(query, (email, name))
            row = await result.fetchone()
            return dict(row)
