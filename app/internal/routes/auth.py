"""Роутер аутентификации — login, refresh, logout."""

from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, status

from app.internal.models.token.api import (
    LoginAPIRequest,
    RefreshTokenAPIRequest,
    TokenAPIResponse,
)
from app.internal.service.token import TokenService

router = APIRouter(route_class=DishkaRoute)


@router.post(
    "/login",
    response_model=TokenAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Вход в систему",
    description="Аутентифицирует пользователя и возвращает пару access/refresh токенов.",
    responses={
        200: {"description": "Токены выданы"},
        401: {"description": "Неверный логин или пароль"},
        422: {"description": "Ошибка валидации"},
    },
)
async def login(
    body: LoginAPIRequest,
    service: Annotated[TokenService, FromDishka()],
) -> TokenAPIResponse:
    return await service.login(body)


@router.post(
    "/refresh",
    response_model=TokenAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить токены",
    description="Принимает refresh token и возвращает новую пару токенов (Refresh Token Rotation).",
    responses={
        200: {"description": "Новые токены выданы"},
        401: {"description": "Невалидный или истёкший refresh token"},
    },
)
async def refresh(
    body: RefreshTokenAPIRequest,
    service: Annotated[TokenService, FromDishka()],
) -> TokenAPIResponse:
    return await service.refresh(body)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из системы",
    description="Отзывает refresh token. Access token продолжает действовать до истечения TTL.",
    responses={
        204: {"description": "Успешный выход"},
        401: {"description": "Невалидный refresh token"},
    },
)
async def logout(
    body: RefreshTokenAPIRequest,
    service: Annotated[TokenService, FromDishka()],
) -> None:
    await service.logout(body.refresh_token)

