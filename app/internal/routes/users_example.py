"""Роутер пользователей — делегирует бизнес-логику в UserService."""

from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Query
from pydantic import TypeAdapter

from app.internal.models.user.api import CreateUserRequest, UpdateUserRequest
from app.internal.models.user.repo import UserListResponse, UserResponse
from app.internal.service.user import UserService

router = APIRouter(route_class=DishkaRoute)

# TypeAdapter для batch-валидации списков — быстрее чем UserResponse(**item) в цикле
_user_list_adapter = TypeAdapter(list[UserResponse])


@router.get(
    "/",
    response_model=UserListResponse,
    summary="Получить список пользователей",
    description="Возвращает пагинированный список пользователей",
)
async def list_users(
    service: Annotated[UserService, FromDishka()],
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(50, ge=1, le=100, description="Размер страницы"),
) -> UserListResponse:
    """Получить список пользователей с пагинацией."""
    result = await service.list_paginated(page=page, page_size=page_size)
    return UserListResponse(
        items=_user_list_adapter.validate_python(result["items"]),
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        pages=result["pages"],
    )


@router.get(
    "/cursor",
    summary="Получить список пользователей (cursor-based)",
    description="Cursor-based пагинация — эффективна для глубоких страниц",
)
async def list_users_cursor(
    service: Annotated[UserService, FromDishka()],
    cursor: str | None = Query(None, description="Cursor (created_at последнего элемента)"),
    limit: int = Query(50, ge=1, le=100, description="Количество записей"),
):
    """Получить список пользователей с cursor-based пагинацией."""
    result = await service.list_cursor(cursor=cursor, limit=limit)
    return {
        "items": _user_list_adapter.validate_python(result["items"]),
        "next_cursor": result["next_cursor"],
        "has_more": result["has_more"],
    }


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Получить пользователя по ID",
    description="Возвращает детальную информацию о пользователе",
    responses={404: {"description": "Пользователь не найден"}},
)
async def get_user(
    user_id: UUID,
    service: Annotated[UserService, FromDishka()],
) -> UserResponse:
    """Получить пользователя по ID."""
    user = await service.get_by_id(user_id)
    return UserResponse(**user)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=201,
    summary="Создать пользователя",
    description="Создаёт нового пользователя с валидацией уникальности email",
    responses={409: {"description": "Email уже существует"}},
)
async def create_user(
    body: CreateUserRequest,
    service: Annotated[UserService, FromDishka()],
) -> UserResponse:
    """Создать нового пользователя."""
    user = await service.create(body)
    return UserResponse(**user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Обновить пользователя",
    description="Обновляет поля пользователя (partial update)",
    responses={
        404: {"description": "Пользователь не найден"},
        409: {"description": "Email уже существует"},
    },
)
async def update_user(
    user_id: UUID,
    body: UpdateUserRequest,
    service: Annotated[UserService, FromDishka()],
) -> UserResponse:
    """Обновить пользователя."""
    user = await service.update(user_id, body)
    return UserResponse(**user)


@router.delete(
    "/{user_id}",
    status_code=204,
    summary="Удалить пользователя",
    description="Удаляет пользователя по ID",
    responses={404: {"description": "Пользователь не найден"}},
)
async def delete_user(
    user_id: UUID,
    service: Annotated[UserService, FromDishka()],
) -> None:
    """Удалить пользователя."""
    await service.delete(user_id)
