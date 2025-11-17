from motor.motor_asyncio import AsyncIOMotorClient
from app.config.main_cfg import settings

"""
Конфигурационный модуль для подключения к MongoDB.
Создает асинхронное подключение к базе данных MongoDB используя настройки из главного конфига.
"""
client = AsyncIOMotorClient(settings.MONGO_URI)
mongo_db = client["ai_tutor"]