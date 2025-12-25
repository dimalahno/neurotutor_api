from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.chat import ChatMessage, ChatStart
from app.services.chat_service import send_chat_message, start_chat

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/start")
async def chat_start(
    payload: ChatStart,
    session: AsyncSession = Depends(get_session),
) -> dict:
    data = await start_chat(session, lesson_id=payload.lesson_id, user_id=payload.user_id)
    return data


@router.post("/message")
async def chat_message(
    payload: ChatMessage,
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await send_chat_message(session, session_id=payload.session_id, text=payload.text)
