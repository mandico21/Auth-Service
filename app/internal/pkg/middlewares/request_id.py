"""Middleware для Request ID - трейсинг и корреляция запросов (Pure ASGI)."""

from __future__ import annotations

import contextvars
import re
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

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


def _get_header(scope: Scope, header_name: str) -> str | None:
    """Извлечь значение заголовка из ASGI scope."""
    header_name_lower = header_name.lower().encode("latin-1")
    for key, value in scope.get("headers", []):
        if key == header_name_lower:
            return value.decode("latin-1")
    return None


class RequestIdMiddleware:
    """
    Pure ASGI middleware для присвоения уникального request ID каждому запросу.

    Преимущества над BaseHTTPMiddleware:
    - Не буферизует тело ответа в память (поддержка streaming)
    - Не ломает background tasks
    - Меньше overhead на каждый запрос
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Получаем или генерируем request ID (с валидацией формата)
        request_id = _get_header(scope, REQUEST_ID_HEADER)
        if not request_id or not _is_valid_request_id(request_id):
            request_id = str(uuid.uuid4())

        # Сохраняем в контексте
        token = _request_id_ctx.set(request_id)

        # Сохраняем в scope state для хендлеров
        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id

        async def send_with_request_id(message: Message) -> None:
            """Добавить X-Request-ID в заголовки ответа."""
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append(
                    (REQUEST_ID_HEADER.lower().encode("latin-1"), request_id.encode("latin-1"))
                )
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            _request_id_ctx.reset(token)
