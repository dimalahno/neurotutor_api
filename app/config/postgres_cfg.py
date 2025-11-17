from app.config.main_cfg import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

"""
Модуль конфигурации PostgreSQL.
Содержит настройки подключения к базе данных PostgreSQL и создание сессий для работы с БД.
"""

# URL подключения к базе данных PostgreSQL, формируется из параметров в файле настроек
DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# Создание движка базы данных PostgreSQL
postgres_db_engine = create_engine(DATABASE_URL)

# Создание фабрики сессий для работы с базой данных
# autocommit=False - автоматическая фиксация транзакций выключена
# autoflush=False - автоматическая синхронизация с БД выключена
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_db_engine)