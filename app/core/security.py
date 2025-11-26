from passlib.context import CryptContext

"""Инициализация контекста для хеширования паролей"""
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Хеширует пароль
    Args:
        password: Пароль в открытом виде
    Returns:
        str: Хешированный пароль
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str | None) -> bool:
    """
    Проверяет соответствие пароля его хешу
    Args:
        plain_password: Пароль в открытом виде
        password_hash: Хеш пароля для проверки
    Returns:
        bool: True если пароль соответствует хешу, иначе False
    """
    if not password_hash:
        return False
    return pwd_context.verify(plain_password, password_hash)
