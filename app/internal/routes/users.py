"""Роутер пользователей — создание и получение пользователей."""

from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request, Response

from app.internal.models.user.api import (
    CreateUserAPIRequest,
    CreateUserAPIResponse,
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
