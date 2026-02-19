"""Global point to cached settings."""

from app.pkg.settings.settings import (
    APISettings,
    PostgresSettings,
    RedisSettings,
    Settings,
    get_settings,
)

__all__ = [
    "APISettings",
    "PostgresSettings",
    "RedisSettings",
    "Settings",
    "get_settings",
    "settings",
]

settings: Settings = get_settings()
