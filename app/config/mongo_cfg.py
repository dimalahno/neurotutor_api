from motor.motor_asyncio import AsyncIOMotorClient
from app.config.main_cfg import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
mongo_db = client["ai_tutor"]