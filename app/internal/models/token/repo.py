__all__ = [
    "CreateRefreshTokenRepoCommand",
    "GetRefreshTokenByJtiRepoQuery",
    "RevokeRefreshTokenRepoCommand",
    "RefreshTokenRepoResponse",
]


from app.internal.models.token import TokenFields, BaseToken
from app.pkg.models.base import BaseModel


# COMMAND
class CreateRefreshTokenRepoCommand(BaseToken):
    """Команда создания refresh token в БД."""

    user_id: TokenFields.user_id
    jti: TokenFields.jti
    expires_at: TokenFields.expires_at


class RevokeRefreshTokenRepoCommand(BaseToken):
    """Команда отзыва refresh token по jti."""

    jti: TokenFields.jti


# QUERY
class GetRefreshTokenByJtiRepoQuery(BaseModel):
    """Запрос получения refresh token по jti."""

    jti: TokenFields.jti


# RESPONSE
class RefreshTokenRepoResponse(BaseToken):
    """Ответ репозитория с данными refresh token."""

    id: int
    user_id: TokenFields.user_id
    jti: TokenFields.jti
    expires_at: TokenFields.expires_at
    revoked: TokenFields.revoked
    created_at: TokenFields.created_at

