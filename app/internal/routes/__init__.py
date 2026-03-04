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
        /api/v1/auth       - Аутентификация (login, refresh, logout)
        /api/v1/users      - Управление пользователями
    """
    from app.internal.routes.auth import router as auth_router
    from app.internal.routes.users import router as users_router
    from app.internal.routes.permissions import router as permissions_router

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
    app.include_router(permissions_router, prefix="/api/v1/permissions", tags=["permissions"])
