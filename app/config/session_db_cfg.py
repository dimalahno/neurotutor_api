from app.config.postgres_cfg import SessionLocal

"""
Модуль конфигурации сессии базы данных.
Предоставляет функционал для создания и управления сессиями PostgreSQL.
"""

def get_db():
    """
    Генератор для создания и управления сессией базы данных.

    Yields:
        SessionLocal: Объект сессии базы данных PostgreSQL

    Note:
        Автоматически закрывает сессию после использования
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()