"""Настройка логирования для приложения.

Поддерживает два формата:
- text: человекочитаемый (для разработки)
- json: structured logging (для ELK/Loki/Grafana в production)

Формат определяется переменной окружения LOG_FORMAT (text|json).
"""

import json
import logging
import sys
from datetime import datetime, timezone
from enum import StrEnum
from typing import cast

__all__ = ["get_logger", "LogType", "CustomLogger"]

_TEXT_FORMAT = (
    "%(asctime)s - [%(levelname)s] - %(name)s - "
    "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
)

# Уровень логирования по умолчанию (можно переопределить через env)
_DEFAULT_LEVEL = "INFO"


class LogType(StrEnum):
    """Типы логов для специальной обработки."""

    BUSINESS = "BUSINESS_VALUABLE_LOG"


class JsonFormatter(logging.Formatter):
    """
    Structured JSON formatter для production.

    Каждая строка лога — валидный JSON с полями:
    - timestamp, level, logger, message, filename, function, line
    - request_id (если доступен из contextvars)
    - exc_info (если есть исключение)
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Добавляем request_id если доступен
        try:
            from app.internal.pkg.middlewares.request_id import get_request_id
            request_id = get_request_id()
            if request_id:
                log_data["request_id"] = request_id
        except ImportError:
            pass

        # Добавляем exception info
        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Дополнительные поля из extra
        for key in ("user_id", "duration_ms", "status_code", "method", "path"):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        return json.dumps(log_data, ensure_ascii=False, default=str)


class CustomLogger(logging.Logger):
    """Расширенный логгер с кастомными методами."""

    def business(self, msg: str, *args, **kwargs) -> None:
        """
        Бизнес-важный лог (для алертов в Telegram и т.д.).

        Логирует с уровнем WARNING и префиксом BUSINESS_VALUABLE_LOG.
        """
        msg = f"{LogType.BUSINESS} {msg}"
        super().warning(msg, *args, **kwargs)


def _create_handler(log_format: str) -> logging.StreamHandler:
    """Создать stream handler с нужным форматом."""
    handler = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(_TEXT_FORMAT))
    return handler


def get_logger(name: str, level: str | None = None) -> CustomLogger:
    """
    Получить настроенный логгер.

    Формат вывода определяется переменной LOG_FORMAT:
    - "text" (по умолчанию) — человекочитаемый формат
    - "json" — structured JSON для production (ELK/Loki/Grafana)

    Аргументы:
        name: Имя логгера (обычно __name__)
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    import os

    # Регистрируем кастомный класс логгера
    logging.setLoggerClass(CustomLogger)

    logger = cast(CustomLogger, logging.getLogger(name))

    # Добавляем handler только если его нет
    if not logger.handlers:
        log_format = os.getenv("LOG_FORMAT", "text").lower()
        logger.addHandler(_create_handler(log_format))

    # Определяем уровень: аргумент > env > default
    log_level = level or os.getenv("LOG_LEVEL", _DEFAULT_LEVEL)
    logger.setLevel(log_level.upper())

    return logger
