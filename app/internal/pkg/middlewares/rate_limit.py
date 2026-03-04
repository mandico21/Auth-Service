"""
Rate limiting middleware (Pure ASGI) — Redis sliding window.

Ограничивает количество запросов с одного IP за окно времени.
Использует Redis INCR + EXPIRE для атомарного подсчёта (sliding window counter).
Если Redis недоступен — пропускает запрос (fail-open), чтобы не блокировать сервис.
"""

from __future__ import annotations

import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.pkg.logger import get_logger


__all__ = ["RateLimitMiddleware"]

logger = get_logger(__name__)


class RateLimitMiddleware:
    """
    Pure ASGI rate limiter.

    Redis получается лениво из Dishka DI контейнера приложения.
    Если Redis недоступен или выключен — fail-open (запрос пропускается).

    Параметры:
        app: ASGI приложение
        max_requests: максимум запросов за window (по умолчанию 100)
        window: окно в секундах (по умолчанию 60)
        key_prefix: префикс ключа в Redis
    """

    def __init__(
        self,
        app: ASGIApp,
        max_requests: int = 100,
        window: int = 60,
        key_prefix: str = "rl",
    ) -> None:
        self.app = app
        self._max_requests = max_requests
        self._window = window
        self._key_prefix = key_prefix

    def _get_client_ip(self, scope: Scope) -> str:
        """Извлечь IP клиента из ASGI scope."""
        # X-Forwarded-For (за reverse proxy)
        for key, value in scope.get("headers", []):
            if key == b"x-forwarded-for":
                # Берём первый IP (реальный клиент)
                return value.decode("latin-1").split(",")[0].strip()
            if key == b"x-real-ip":
                return value.decode("latin-1").strip()
        # Fallback: прямое подключение
        client = scope.get("client")
        if client:
            return client[0]
        return "unknown"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        # Пропускаем health check и метрики
        if path.startswith("/health") or path == "/metrics":
            await self.app(scope, receive, send)
            return


        client_ip = self._get_client_ip(scope)
        key = f"{self._key_prefix}:{client_ip}"

        # Получаем Redis из Dishka DI контейнера приложения
        try:
            app_state = scope.get("app")
            if not app_state or not hasattr(app_state, "state"):
                await self.app(scope, receive, send)
                return
            container = getattr(app_state.state, "dishka_container", None)
            if container is None:
                await self.app(scope, receive, send)
                return

            from app.pkg.connectors.redis import RedisConnector
            async with container() as di_scope:
                redis_connector = await di_scope.get(RedisConnector)
                async with redis_connector.connect() as redis_client:
                    # Атомарный INCR + EXPIRE
                    current = await redis_client.incr(key)
                    if current == 1:
                        await redis_client.expire(key, self._window)
                    ttl = await redis_client.ttl(key)
        except Exception:
            # Redis недоступен — fail-open
            await self.app(scope, receive, send)
            return

        # Добавляем заголовки rate limit в ответ
        remaining = max(0, self._max_requests - current)

        if current > self._max_requests:
            # 429 Too Many Requests
            logger.warning(
                "Rate limit exceeded: ip=%s, current=%d, limit=%d",
                client_ip,
                current,
                self._max_requests,
            )
            body = json.dumps({
                "message": "Слишком много запросов",
                "details": {
                    "limit": self._max_requests,
                    "window_seconds": self._window,
                    "retry_after": max(ttl, 1),
                },
            }).encode("utf-8")

            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("latin-1")),
                    (b"retry-after", str(max(ttl, 1)).encode("latin-1")),
                    (b"x-ratelimit-limit", str(self._max_requests).encode("latin-1")),
                    (b"x-ratelimit-remaining", b"0"),
                    (b"x-ratelimit-reset", str(max(ttl, 1)).encode("latin-1")),
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return

        # Пропускаем запрос, добавляя rate limit заголовки
        async def send_with_ratelimit(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([
                    (b"x-ratelimit-limit", str(self._max_requests).encode("latin-1")),
                    (b"x-ratelimit-remaining", str(remaining).encode("latin-1")),
                    (b"x-ratelimit-reset", str(max(ttl, 1)).encode("latin-1")),
                ])
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_ratelimit)



