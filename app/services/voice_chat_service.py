from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from bson import ObjectId
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.mongo_cfg import mongo_db
from app.services.llm_service import chat_client
from app.services.llm_utils.compact_lesson_context import extract_compact_context
from app.services.llm_utils.prompt_builder import build_system_prompt
from app.services.user_service import UserService

from app.services.llm_voice_service import (
    build_realtime_session_config,
    create_webrtc_call,
    hangup_call,
)

logger = logging.getLogger(__name__)

VOICE_COLLECTION = mongo_db.voice_sessions
LESSONS_COLLECTION = mongo_db.lessons


def _validate_object_id(raw_id: str) -> ObjectId:
    try:
        return ObjectId(raw_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ObjectId format")


async def _fetch_lesson_doc(lesson_id: str) -> Dict[str, Any]:
    oid = _validate_object_id(lesson_id)
    doc = await LESSONS_COLLECTION.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return doc


async def start_voice_chat(
    session: AsyncSession,
    *,
    lesson_id: str,
    user_id: int,
    voice: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    svc = UserService()
    user = await svc.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    lesson = await _fetch_lesson_doc(lesson_id)
    ctx = extract_compact_context(lesson)
    system_prompt = build_system_prompt(ctx)

    # Текстовый greeting — удобен для UI (и для первого client-event на data channel).
    # Голос "сам" не начнётся, пока клиент не пошлёт событие, поэтому greeting отдаём явно.
    greeting = await chat_client(
        system_prompt,
        [
            {
                "role": "user",
                "content": (
                    "Start the conversation with a short greeting related to the lesson "
                    "topic and ask one simple question."
                ),
            }
        ],
    )

    doc = {
        "lesson_id": lesson_id,
        "user_id": user_id,
        "system_prompt": system_prompt,
        "realtime": {
            "model": model,
            "voice": voice,
            "call_id": None,
        },
        "state": {
            "greeting": greeting,
            "status": "created",
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    result = await VOICE_COLLECTION.insert_one(doc)

    return {
        "session_id": str(result.inserted_id),
        "greeting": greeting,
        "status": "created",
    }


async def create_call_from_offer(
    session: AsyncSession,
    *,
    session_id: str,
    user_id: int,
    sdp_offer: str,
) -> Dict[str, Any]:
    oid = _validate_object_id(session_id)

    voice_doc = await VOICE_COLLECTION.find_one({"_id": oid})
    if not voice_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if int(voice_doc.get("user_id") or 0) != int(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    system_prompt: str = voice_doc.get("system_prompt") or ""
    rt = voice_doc.get("realtime") or {}
    model = rt.get("model") or "gpt-realtime"
    voice = rt.get("voice") or "marin"

    session_cfg = build_realtime_session_config(
        instructions=system_prompt,
        model=model,
        voice=voice,
        max_output_tokens=300,
    )

    call_res = await create_webrtc_call(sdp_offer=sdp_offer, session_config=session_cfg)

    update_data = {
        "realtime.call_id": call_res.call_id,
        "realtime.model": model,
        "realtime.voice": voice,
        "state.status": "active",
        "updated_at": datetime.now(),
    }
    await VOICE_COLLECTION.update_one({"_id": oid}, {"$set": update_data})

    return {
        "session_id": session_id,
        "call_id": call_res.call_id,
        "sdp_answer": call_res.sdp_answer,
        "status": "active",
    }


async def stop_voice_chat(
    session: AsyncSession,
    *,
    session_id: str,
    user_id: int,
) -> Dict[str, Any]:
    oid = _validate_object_id(session_id)

    voice_doc = await VOICE_COLLECTION.find_one({"_id": oid})
    if not voice_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if int(voice_doc.get("user_id") or 0) != int(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    call_id = (voice_doc.get("realtime") or {}).get("call_id")
    if call_id:
        await hangup_call(call_id)

    update_data = {
        "state.status": "ended",
        "updated_at": datetime.now(),
        "ended_at": datetime.now(),
    }
    await VOICE_COLLECTION.update_one({"_id": oid}, {"$set": update_data})

    return {"session_id": session_id, "status": "ended"}
