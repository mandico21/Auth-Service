"""Middleware для таймаута запросов - защита от зависших запросов."""

from __future__ import annotations

import asyncio
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.internal.pkg.middlewares.request_id import get_request_id
from app.pkg.logger import get_logger

__all__ = ["TimeoutMiddleware"]

logger = get_logger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware для ограничения времени выполнения запроса.
    Возвращает 504 Gateway Timeout если запрос превышает таймаут.

    При таймауте обработчик не отменяется (asyncio.shield): запрос продолжает
    выполняться в фоне до завершения, чтобы соединения БД/пулы корректно
    освобождались и не утекали при CancelledError.
    """

    def __init__(self, app, timeout: int = 30):
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        task = asyncio.create_task(call_next(request))
        try:
            return await asyncio.wait_for(
                asyncio.shield(task),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            request_id = get_request_id() or ""
            logger.warning(
                "Request timeout after %ds (request_id=%s); handler continues in background",
                self.timeout,
                request_id,
            )
            return JSONResponse(
                status_code=504,
                content={
                    "message": "Превышено время ожидания запроса",
                    "details": {"timeout_seconds": self.timeout},
                },
            )
