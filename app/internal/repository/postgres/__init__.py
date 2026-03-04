"""PostgreSQL репозитории."""
from app.internal.repository.postgres.user import UserRepo
from app.internal.repository.postgres.user2 import UserRepository
from app.internal.repository.postgres.refresh_token import RefreshTokenRepo
from app.internal.repository.postgres.permission import PermissionRepo

__all__ = ["UserRepository", "UserRepo", "RefreshTokenRepo", "PermissionRepo"]
