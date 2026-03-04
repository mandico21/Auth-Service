"""Middleware для таймаута запросов - защита от зависших запросов (Pure ASGI)."""

from __future__ import annotations

import asyncio
import json

from starlette.types import ASGIApp, Receive, Scope, Send

from app.internal.pkg.middlewares.request_id import get_request_id
from app.pkg.logger import get_logger

__all__ = ["TimeoutMiddleware"]

logger = get_logger(__name__)


class TimeoutMiddleware:
    """
    Pure ASGI middleware для ограничения времени выполнения запроса.
    Возвращает 504 Gateway Timeout если запрос превышает таймаут.

    Преимущества над BaseHTTPMiddleware:
    - Не буферизирует тело ответа (поддержка streaming)
    - Не ломает background tasks
    - Меньше overhead на каждый запрос

    При таймауте обработчик отменяется, чтобы не накапливать фоновые задачи
    и не удерживать ресурсы (соединения/память) дольше необходимого.
    """

    def __init__(self, app: ASGIApp, timeout: int = 30) -> None:
        self.app = app
        self.timeout = timeout

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            await asyncio.wait_for(
                self.app(scope, receive, send),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            request_id = get_request_id() or ""
            logger.warning(
                "Request timeout after %ds (request_id=%s); handler cancelled",
                self.timeout,
                request_id,
            )

            body = json.dumps({
                "message": "Превышено время ожидания запроса",
                "details": {"timeout_seconds": self.timeout},
            }).encode("utf-8")

            await send({
                "type": "http.response.start",
                "status": 504,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("latin-1")),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": body,
            })
