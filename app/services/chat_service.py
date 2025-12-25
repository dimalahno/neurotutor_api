from logging import Logger
from typing import Dict, Any

from bson import ObjectId
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.mongo_cfg import mongo_db
from app.services.user_service import UserService
from app.services.llm_utils.compact_lesson_context import extract_compact_context
from app.services.llm_utils.prompt_builder import build_system_prompt

logger = Logger(__name__)

async def _fetch_lesson_doc(lesson_id: str) -> Dict[str, Any]:
    try:
        oid = ObjectId(lesson_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ObjectId format",
        )

    doc = await mongo_db.lessons.find_one({"_id": oid})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )
    return doc

async def start_chat(session: AsyncSession, lesson_id: str, user_id: int) -> str:
    svc = UserService()
    user =  await svc.get_user_by_id(session, user_id)

    lesson = await _fetch_lesson_doc(lesson_id)
    ctx = extract_compact_context(lesson)
    system_prompt = build_system_prompt(ctx)
    return system_prompt