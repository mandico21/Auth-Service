"""Роутер аутентификации — login, refresh, logout."""

from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.internal.models.token.api import (
    LoginAPIRequest,
    RefreshTokenAPIRequest,
    TokenAPIResponse,
)
from app.internal.pkg.middlewares.auth import CurrentUserID
from app.internal.service.token import TokenService

router = APIRouter(route_class=DishkaRoute)


@router.post(
    "/token",
    response_model=TokenAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="OAuth2 token (для Swagger UI)",
    description=(
        "OAuth2-совместимый эндпоинт для получения токена через form-data. "
        "Используется кнопкой **Authorize** в Swagger UI. "
        "Для API-клиентов используйте `/login`."
    ),
    include_in_schema=True,
    tags=["auth"],
)
async def oauth2_token(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[TokenService, FromDishka()],
) -> TokenAPIResponse:
    return await service.login(LoginAPIRequest(username=form.username, password=form.password))


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


@router.post(
    "/logout/all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход со всех устройств",
    description=(
        "Отзывает все активные refresh токены текущего пользователя. "
        "Access токены продолжают действовать до истечения своего TTL."
    ),
    responses={
        204: {"description": "Все сессии завершены"},
        401: {"description": "Не авторизован"},
    },
)
async def logout_all(
    service: Annotated[TokenService, FromDishka()],
    current_user_id: CurrentUserID,
) -> None:
    await service.revoke_all_sessions(str(current_user_id))


