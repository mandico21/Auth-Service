"""Роутер разрешений — CRUD и управление привязкой к пользователям."""

from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, status

from app.internal.models.permissions.api import (
    AssignPermissionAPIRequest,
    CreatePermissionAPIRequest,
    PermissionAPIResponse,
    UserPermissionsAPIResponse,
)
from app.internal.pkg.middlewares.auth import CurrentUserID
from app.internal.pkg.middlewares.permission import require_permission
from app.internal.service.permission import PermissionService

router = APIRouter(route_class=DishkaRoute)


@router.post(
    "/",
    response_model=PermissionAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать разрешение",
    description="Создаёт новое разрешение. Требует права `manage_permissions`.",
    dependencies=[require_permission("manage_permissions")],
    responses={
        201: {"description": "Разрешение успешно создано"},
        401: {"description": "Не авторизован"},
        403: {"description": "Недостаточно прав"},
        409: {"description": "Разрешение с таким кодом уже существует"},
    },
)
async def create_permission(
    body: CreatePermissionAPIRequest,
    service: Annotated[PermissionService, FromDishka()],
    _: CurrentUserID,
) -> PermissionAPIResponse:
    return await service.create(body)


@router.get(
    "/",
    response_model=list[PermissionAPIResponse],
    status_code=status.HTTP_200_OK,
    summary="Список всех разрешений",
    responses={
        200: {"description": "Список разрешений"},
        401: {"description": "Не авторизован"},
    },
)
async def list_permissions(
    service: Annotated[PermissionService, FromDishka()],
    _: CurrentUserID,
) -> list[PermissionAPIResponse]:
    return await service.list_all()


@router.get(
    "/{code}",
    response_model=PermissionAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить разрешение по коду",
    responses={
        200: {"description": "Данные разрешения"},
        401: {"description": "Не авторизован"},
        404: {"description": "Разрешение не найдено"},
    },
)
async def get_permission(
    code: str,
    service: Annotated[PermissionService, FromDishka()],
    _: CurrentUserID,
) -> PermissionAPIResponse:
    return await service.read_by_code(code)


@router.post(
    "/{code}/assign",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Назначить разрешение пользователю",
    description="Назначает разрешение указанному пользователю. Требует права `manage_permissions`.",
    dependencies=[require_permission("manage_permissions")],
    responses={
        204: {"description": "Разрешение назначено"},
        401: {"description": "Не авторизован"},
        403: {"description": "Недостаточно прав"},
        404: {"description": "Разрешение не найдено"},
    },
)
async def assign_permission(
    code: str,
    body: AssignPermissionAPIRequest,
    service: Annotated[PermissionService, FromDishka()],
    _: CurrentUserID,
) -> None:
    await service.assign_to_user(code=code, user_id=body.user_id)


@router.delete(
    "/{code}/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отозвать разрешение у пользователя",
    description="Отзывает разрешение у указанного пользователя. Требует права `manage_permissions`.",
    dependencies=[require_permission("manage_permissions")],
    responses={
        204: {"description": "Разрешение отозвано"},
        401: {"description": "Не авторизован"},
        403: {"description": "Недостаточно прав"},
        404: {"description": "Разрешение не найдено"},
    },
)
async def revoke_permission(
    code: str,
    body: AssignPermissionAPIRequest,
    service: Annotated[PermissionService, FromDishka()],
    _: CurrentUserID,
) -> None:
    await service.revoke_from_user(code=code, user_id=body.user_id)


@router.get(
    "/users/{user_id}",
    response_model=UserPermissionsAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Список разрешений пользователя",
    responses={
        200: {"description": "Разрешения пользователя"},
        401: {"description": "Не авторизован"},
    },
)
async def get_user_permissions(
    user_id: UUID,
    service: Annotated[PermissionService, FromDishka()],
    _: CurrentUserID,
) -> UserPermissionsAPIResponse:
    return await service.get_user_permissions(user_id=user_id)
