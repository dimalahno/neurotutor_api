"""
Основной конфигурационный модуль приложения.
Содержит настройки для подключения к базам данных и параметры запуска приложения.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Базовый путь к директории приложения (указывает на `app/`)
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """
    Класс настроек приложения.
    Загружает конфигурацию из переменных окружения или .env файла.
    """
    APP_HOST: str
    APP_PORT: int
    DEBUG_MODE: bool

    MONGO_URI: str

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    OPEN_AI_API_KEY: str

    MINIO_ENDPOINT: str
    MINIO_BUCKET: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_REGION: str

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8"
    )
settings = Settings()