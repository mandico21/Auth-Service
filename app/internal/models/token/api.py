__all__ = [
    "LoginAPIRequest",
    "TokenAPIResponse",
    "RefreshTokenAPIRequest",
]

from app.internal.models.token import TokenFields, BaseToken
from app.internal.models.user import UserFields


# REQUEST
class LoginAPIRequest(BaseToken):
    """Запрос на аутентификацию пользователя."""

    username: UserFields.username
    password: UserFields.password


class RefreshTokenAPIRequest(BaseToken):
    """Запрос на обновление токенов."""

    refresh_token: TokenFields.refresh_token


# RESPONSE
class TokenAPIResponse(BaseToken):
    """Ответ с парой access/refresh токенов."""

    access_token: TokenFields.access_token
    refresh_token: TokenFields.refresh_token
    token_type: TokenFields.token_type = "bearer"

