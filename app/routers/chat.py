from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.services.chat_service import start_chat

router = APIRouter(prefix="/chat", tags=["chat"])


# 694395b45e2a9fe2fe6d4205
# 69413f53fb9995b3450fad1b
@router.post("/start/{lesson_id}/{user_id}")
async def api_start_chat(
    lesson_id: str,
    user_id: int,
    session: AsyncSession = Depends(get_session),
) -> str:
    data = await start_chat(session, lesson_id=lesson_id, user_id=user_id)
    return data
