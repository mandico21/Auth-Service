"""PostgreSQL репозитории."""
from app.internal.repository.postgres.user import UserRepo
from app.internal.repository.postgres.user2 import UserRepository

__all__ = ["UserRepository", "UserRepo"]
