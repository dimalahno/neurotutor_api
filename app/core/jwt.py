"""
Модуль для работы с JWT токенами.

Содержит функции для создания и проверки JWT токенов аутентификации.
Поддерживает создание как access, так и refresh токенов.
"""

from datetime import datetime, timedelta
import jwt

from app.config.main_cfg import settings
from app.models.user_models import User


def create_access_token(user: User, expires_delta: timedelta | None = None) -> str:
    """
    Создает JWT access token.

    Args:
        sub: Идентификатор субъекта токена (обычно user_id)
        expires_delta: Срок действия токена. Если не указан, используется ACCESS_TOKEN_EXPIRE_MINUTES

    Returns:
        str: Закодированный JWT токен
        :param expires_delta:
        :param user:
    """

    now = datetime.now()
    exp = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "roles": [r.code for r in user.roles],   # добавили роли
        "iat": now,
        "exp": exp,
        "type": "access",
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    """
    Создает JWT refresh token.

    Args:
        sub: Идентификатор субъекта токена (обычно user_id)
        expires_delta: Срок действия токена. Если не указан, используется REFRESH_TOKEN_EXPIRE_DAYS

    Returns:
        str: Закодированный JWT токен
        :param expires_delta:
        :param user_id:
    """

    now = datetime.now()
    exp = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": exp,
        "type": "refresh",
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    """
    Декодирует и проверяет JWT токен.

    Args:
        token: JWT токен для декодирования

    Returns:
        dict: Полезная нагрузка токена в виде словаря

    Raises:
        jwt.InvalidTokenError: Если токен недействителен или истек срок его действия
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
