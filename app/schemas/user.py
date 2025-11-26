from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """
    Модель данных для создания нового пользователя.

    Attributes:
        email: Email пользователя
        password: Пароль пользователя
        first_name: Имя пользователя
        last_name: Фамилия пользователя  
        middle_name: Отчество пользователя (опционально)
    """
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None


class UserOut(BaseModel):
    """
    Модель данных для отображения информации о пользователе.

    Attributes:
        id: Уникальный идентификатор пользователя
        email: Email пользователя
        first_name: Имя пользователя
        last_name: Фамилия пользователя
        middle_name: Отчество пользователя (опционально)
        status_id: Идентификатор статуса пользователя
        created_at: Дата и время создания записи
        updated_at: Дата и время последнего обновления
    """
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    status_id: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None

class TokenPair(BaseModel):
    """
    Модель данных для пары токенов аутентификации.

    Attributes:
        access_token: Токен доступа
        refresh_token: Токен обновления
        token_type: Тип токена (по умолчанию "bearer")
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
