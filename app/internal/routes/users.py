"""Роутер пользователей — создание и получение пользователей."""

from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request, Response

from app.internal.models.user.api import (
    ChangePasswordAPIRequest,
    CreateUserAPIRequest,
    CreateUserAPIResponse,
    MeAPIResponse,
    ResetPasswordAPIRequest,
    UpdateProfileAPIRequest,
    UpdateProfileAPIResponse,
    UpdateUserStatusAPIRequest,
    UserAPIResponse,
    ReadUserByUsernameAPIRequest,
)
from app.internal.pkg.middlewares.auth import CurrentUserID
from app.internal.service.user import UserService

router = APIRouter(route_class=DishkaRoute)


@router.post(
    "/",
    response_model=CreateUserAPIResponse,
    status_code=201,
    summary="Создать пользователя",
    description="Регистрирует нового пользователя. Пароль хешируется через Argon2id.",
    responses={
        201: {"description": "Пользователь успешно создан"},
        401: {"description": "Не авторизован"},
        409: {"description": "Пользователь с таким username или email уже существует"},
        422: {"description": "Ошибка валидации входных данных"},
    },
)
async def create_user(
    body: CreateUserAPIRequest,
    request: Request,
    response: Response,
    service: Annotated[UserService, FromDishka()],
    _: CurrentUserID,
) -> CreateUserAPIResponse:
    user = await service.create(body)
    response.headers["Location"] = str(
        request.url_for("get_user_by_username", username=user.username)
    )
    return user


@router.get(
    "/me",
    response_model=MeAPIResponse,
    summary="Мой профиль",
    description="Возвращает полный профиль текущего авторизованного пользователя с его разрешениями.",
    responses={
        200: {"description": "Профиль пользователя"},
        401: {"description": "Не авторизован"},
    },
)
async def get_me(
    service: Annotated[UserService, FromDishka()],
    current_user_id: CurrentUserID,
) -> MeAPIResponse:
    return await service.get_me(current_user_id)


@router.patch(
    "/me",
    response_model=UpdateProfileAPIResponse,
    summary="Обновить профиль",
    description="Обновляет имя, фамилию и/или email текущего пользователя.",
    responses={
        200: {"description": "Профиль обновлён"},
        401: {"description": "Не авторизован"},
        409: {"description": "Email уже занят другим пользователем"},
        422: {"description": "Ошибка валидации"},
    },
)
async def update_me(
    body: UpdateProfileAPIRequest,
    service: Annotated[UserService, FromDishka()],
    current_user_id: CurrentUserID,
) -> UpdateProfileAPIResponse:
    return await service.update_profile(current_user_id, body)


@router.post(
    "/me/change-password",
    status_code=204,
    summary="Сменить пароль",
    description="Меняет пароль текущего пользователя. Требует ввода текущего пароля.",
    responses={
        204: {"description": "Пароль успешно изменён"},
        401: {"description": "Текущий пароль неверный или не авторизован"},
        422: {"description": "Ошибка валидации"},
    },
)
async def change_password(
    body: ChangePasswordAPIRequest,
    service: Annotated[UserService, FromDishka()],
    current_user_id: CurrentUserID,
) -> None:
    await service.change_password(current_user_id, body)


@router.get(
    "/{username}",
    name="get_user_by_username",
    response_model=UserAPIResponse,
    summary="Получить пользователя по username",
    responses={
        200: {"description": "Данные пользователя"},
        401: {"description": "Не авторизован"},
        404: {"description": "Пользователь не найден"},
    },
)
async def get_user_by_username(
    username: str,
    service: Annotated[UserService, FromDishka()],
    _: CurrentUserID,
) -> UserAPIResponse:
    """Получить пользователя по его username."""
    return await service.read_by_username(ReadUserByUsernameAPIRequest(username=username))


@router.post(
    "/{user_id}/reset-password",
    status_code=204,
    summary="Сбросить пароль пользователя (admin)",
    description="Принудительно устанавливает новый пароль для пользователя. Требует право `manage_users`.",
    responses={
        204: {"description": "Пароль сброшен"},
        401: {"description": "Не авторизован"},
        403: {"description": "Недостаточно прав"},
        404: {"description": "Пользователь не найден"},
        422: {"description": "Ошибка валидации"},
    },
)
async def reset_password(
    user_id: UUID,
    body: ResetPasswordAPIRequest,
    service: Annotated[UserService, FromDishka()],
    current_user_id: CurrentUserID,
) -> None:
    await service.reset_password(user_id, current_user_id, body)


@router.patch(
    "/{user_id}/status",
    response_model=UpdateProfileAPIResponse,
    summary="Изменить статус пользователя (admin)",
    description="Активирует или деактивирует учётную запись пользователя. Требует право `manage_users`.",
    responses={
        200: {"description": "Статус обновлён"},
        401: {"description": "Не авторизован"},
        403: {"description": "Недостаточно прав"},
        404: {"description": "Пользователь не найден"},
        422: {"description": "Ошибка валидации"},
    },
)
async def update_user_status(
    user_id: UUID,
    body: UpdateUserStatusAPIRequest,
    service: Annotated[UserService, FromDishka()],
    current_user_id: CurrentUserID,
) -> UpdateProfileAPIResponse:
    return await service.set_active_status(user_id, current_user_id, body)
