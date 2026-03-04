"""Конфигурация логирования для Uvicorn.

Поддерживает два формата через переменную LOG_FORMAT:
- text (по умолчанию): человекочитаемый формат
- json: structured JSON для ELK/Loki/Grafana
"""

import os


__all__ = ["LOGGING_CONFIG"]

LOG_FORMAT_ENV = os.getenv("LOG_FORMAT", "text").lower()

# Текстовый формат логов
_TEXT_FORMAT = (
    "%(asctime)s - [%(levelname)s] - %(name)s - "
    "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
)


def _build_logging_config() -> dict:
    """Построить конфигурацию логирования в зависимости от LOG_FORMAT."""
    if LOG_FORMAT_ENV == "json":
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "app.pkg.logger.logger.JsonFormatter",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "json",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "access": {
                    "formatter": "json",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
                "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
                "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
            },
        }

    # Default: text format
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": _TEXT_FORMAT},
            "access": {"format": _TEXT_FORMAT},
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        },
    }


LOGGING_CONFIG = _build_logging_config()
