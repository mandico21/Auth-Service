"""Dependency для проверки разрешений (permissions) пользователя."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request

from app.internal.pkg.middlewares.auth import get_current_user_id
from app.internal.service.permission import PermissionService
from app.pkg.models.base import ForbiddenError

_bearer_dep = Depends(get_current_user_id)


def require_permission(code: str) -> Depends:
    """
    Фабрика FastAPI Dependency для проверки разрешения.

    Использование в декораторе роута:
        @router.post("/", dependencies=[require_permission("create_user")])
    """

    async def _check(
        request: Request,
        user_id: Annotated[UUID, _bearer_dep],
    ) -> None:
        service: PermissionService = await request.state.dishka_container.get(
            PermissionService
        )
        allowed = await service.has_permission(user_id=user_id, code=code)
        if not allowed:
            raise ForbiddenError(
                message=f"Недостаточно прав: требуется разрешение '{code}'"
            )

    return Depends(_check)
