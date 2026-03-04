__all__ = [
    "AppError",
    "BadRequestError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "DependencyError",
]

from http import HTTPStatus
from typing import Any


class AppError(Exception):
    """
    Базовая ошибка приложения. Не зависит от Pydantic.
    """
    http_status: int = HTTPStatus.INTERNAL_SERVER_ERROR
    message: str = "Internal server error"
    expose: bool = True  # если False — прячем детализацию от клиента

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        http_status: int | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        expose: bool | None = None,
    ) -> None:
        super().__init__(message or self.message)
        self.http_status = int(http_status or self.http_status)
        self.message = message or self.message
        self.details = details or {}
        self.cause = cause
        if expose is not None:
            self.expose = expose

    def __repr__(self) -> str:
        return f"{type(self).__name__}(status={self.http_status}, message={self.message!r})"


# ── Частые прикладные ошибки ────────────────────────────────────────────────

class BadRequestError(AppError):
    """Неверный запрос (например, при синтаксической ошибке в JSON или при отсутствии обязательных полей)."""
    http_status = HTTPStatus.BAD_REQUEST
    message = "Bad request"


class UnauthorizedError(AppError):
    """Ошибка аутентификации (например, при отсутствии или недействительном токене доступа)."""
    http_status = HTTPStatus.UNAUTHORIZED
    message = "Unauthorized"


class ForbiddenError(AppError):
    """Доступ запрещён (например, при отсутствии прав на ресурс)."""
    http_status = HTTPStatus.FORBIDDEN
    message = "Forbidden"


class NotFoundError(AppError):
    """Ресурс не найден. (Например, при запросе несуществующего объекта по ID)."""
    code = "NOT_FOUND"
    http_status = HTTPStatus.NOT_FOUND
    message = "Resource not found"


class ConflictError(AppError):
    """Конфликт данных (например, при попытке создать ресурс с уже существующим уникальным полем)."""
    http_status = HTTPStatus.CONFLICT
    message = "Conflict"


class UnprocessableEntityError(AppError):
    """Невозможно обработать запрос (например, при нарушении бизнес-правил, даже если синтаксис запроса верный)."""
    http_status = HTTPStatus.UNPROCESSABLE_ENTITY
    message = "Unprocessable entity"


class DependencyError(AppError):
    """Проблема с внешним сервисом/ресурсом (DB/Redis/Rabbit и т.п.)."""
    http_status = HTTPStatus.SERVICE_UNAVAILABLE
    message = "Dependency error"
