from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# указывает на `app/`
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_HOST: str
    APP_PORT: int
    DEBUG_MODE: bool

    MONGO_URI: str

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8"
    )
settings = Settings()