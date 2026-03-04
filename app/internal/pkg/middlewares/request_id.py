"""Middleware для Request ID - трейсинг и корреляция запросов."""

from __future__ import annotations

import contextvars
import re
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

__all__ = ["RequestIdMiddleware", "get_request_id", "REQUEST_ID_HEADER"]

REQUEST_ID_HEADER = "X-Request-ID"
_MAX_REQUEST_ID_LENGTH = 64
_REQUEST_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-_:.]+$")
_request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def _is_valid_request_id(value: str) -> bool:
    """Валидация формата request ID (защита от log injection)."""
    return (
        0 < len(value) <= _MAX_REQUEST_ID_LENGTH
        and _REQUEST_ID_PATTERN.match(value) is not None
    )


def get_request_id() -> str | None:
    """Получить текущий request ID из контекста."""
    return _request_id_ctx.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware для присвоения уникального request ID каждому запросу.
    - Использует заголовок X-Request-ID если он передан и валиден (для распределённого трейсинга)
    - Генерирует UUID4 если заголовок отсутствует или невалиден
    - Добавляет request ID в заголовки ответа
    - Сохраняет в context var для логирования/трейсинга
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Получаем или генерируем request ID (с валидацией формата)
        request_id = request.headers.get(REQUEST_ID_HEADER)
        if not request_id or not _is_valid_request_id(request_id):
            request_id = str(uuid.uuid4())

        # Сохраняем в контексте
        token = _request_id_ctx.set(request_id)

        # Сохраняем в state запроса для хендлеров
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            _request_id_ctx.reset(token)
