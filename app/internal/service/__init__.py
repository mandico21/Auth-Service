"""Сервисный слой приложения.

Сервисы содержат бизнес-логику и оркестрируют работу репозиториев.
"""

from app.internal.service.user import UserService

__all__ = ["UserService"]
