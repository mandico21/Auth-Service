"""Prometheus метрики middleware и эндпоинт (Pure ASGI)."""

from __future__ import annotations

import asyncio
import time

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

__all__ = ["PrometheusMiddleware", "metrics_endpoint"]

# Метрики
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Общее количество HTTP запросов",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Латентность HTTP запросов в секундах",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Количество HTTP запросов в обработке",
    ["method", "endpoint"],
)


def _get_path_template(scope: Scope, app: ASGIApp) -> str:
    """
    Получить шаблон пути для метрик (избегаем взрыва кардинальности).

    Пытаемся получить route path template (например /users/{user_id})
    через matching роутов Starlette/FastAPI.
    """
    # Пробуем получить из scope (если route уже зарезолвлен)
    route = scope.get("route")
    if route and hasattr(route, "path"):
        return route.path

    # Fallback: нормализуем путь, чтобы UUID/числовые ID не создавали уникальные метки
    return "/unknown"


class PrometheusMiddleware:
    """
    Pure ASGI middleware для сбора Prometheus метрик HTTP запросов.

    Преимущества над BaseHTTPMiddleware:
    - Не буферизирует тело ответа (поддержка streaming)
    - Не ломает background tasks
    - Меньше overhead на каждый запрос
    """

    def __init__(self, app: ASGIApp, app_name: str = "fastapi") -> None:
        self.app = app
        self.app_name = app_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/unknown")

        # Пропускаем сам эндпоинт метрик
        if path == "/metrics":
            await self.app(scope, receive, send)
            return

        # Будем определять шаблон пути после обработки (когда route зарезолвлен)
        status_code = 500  # default если ответ не придёт
        start_time = time.perf_counter()
        resolved_path = "/unknown"

        async def send_with_metrics(message: Message) -> None:
            nonlocal status_code, resolved_path
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                # Route уже зарезолвлен к моменту ответа
                resolved_path = _get_path_template(scope, self.app)
            await send(message)

        REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).inc()
        try:
            await self.app(scope, receive, send_with_metrics)
        except Exception:
            resolved_path = _get_path_template(scope, self.app)
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - start_time
            label_path = resolved_path
            REQUEST_COUNT.labels(method=method, endpoint=label_path, status=status_code).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=label_path).observe(duration)
            REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).dec()


async def metrics_endpoint(request: Request) -> Response:
    """Эндпоинт Prometheus метрик. Обновляет pool metrics при каждом scrape."""
    # Обновляем pool metrics если коннекторы доступны через DI
    if hasattr(request.app, "state") and hasattr(request.app.state, "dishka_container"):
        try:
            from app.internal.pkg.middlewares.pool_metrics import update_pool_metrics
            from app.pkg.connectors.postgres import PostgresConnector
            from app.pkg.connectors.redis import RedisConnector

            container = request.app.state.dishka_container
            async with container() as scope:
                postgres = await scope.get(PostgresConnector)
                redis = await scope.get(RedisConnector)
                update_pool_metrics(postgres, redis)
        except Exception:
            pass  # Не блокируем scrape при ошибке

    # generate_latest() — синхронная, может блокировать event loop при большом числе метрик
    content = await asyncio.get_event_loop().run_in_executor(None, generate_latest)

    return Response(
        content=content,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
