"""Регистрация маршрутов приложения."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

__all__ = ["register_routes"]


def register_routes(app: "FastAPI") -> None:
    """
    Регистрация всех маршрутов приложения.

    Централизованная точка для подключения всех API роутеров.
    При добавлении новых роутеров добавляйте их сюда.

    Структура API:
        /api/v1/users      - Управление пользователями
    """
    from app.internal.routes.users import router as users_router
    from app.internal.routes.users_example import router as users_example_router

    app.include_router(
        users_router,
        prefix="/api/v1/users",
        tags=["users"],
    )
    app.include_router(
        users_example_router,
        prefix="/api/v1/users-example",
        tags=["users-example"],
    )
