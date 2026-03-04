"""Утилиты для хеширования и верификации паролей через Argon2id."""

__all__ = ["hash_password", "verify_password", "needs_rehash"]

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def hash_password(plain_password: str) -> str:
    """Хешировать пароль с использованием Argon2id.

    Args:
        plain_password: Открытый пароль пользователя.

    Returns:
        Хеш пароля в формате PHC (включает алгоритм, параметры и соль).
    """
    return _hasher.hash(plain_password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    """Проверить, соответствует ли открытый пароль хешу.

    Args:
        hashed_password: Хеш пароля из базы данных.
        plain_password: Пароль для проверки.

    Returns:
        True если пароль верный, False — иначе.
    """
    try:
        return _hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Проверить, нужно ли перехешировать пароль (если параметры Argon2 устарели).

    Args:
        hashed_password: Хеш пароля из базы данных.

    Returns:
        True если параметры хеша устарели и пароль нужно перехешировать.
    """
    return _hasher.check_needs_rehash(hashed_password)
