from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.mongo_cfg import mongo_db
from app.services.llm_service import chat_client
from app.services.llm_utils.compact_lesson_context import extract_compact_context
from app.services.llm_utils.prompt_builder import build_system_prompt
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

CHAT_COLLECTION = mongo_db.chat_sessions
DEFAULT_HISTORY_LIMIT = 20

def _validate_object_id(raw_id: str) -> ObjectId:
    try:
        return ObjectId(raw_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ObjectId format"
        )


USER_NOT_FOUND_ERROR = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
)


async def _fetch_lesson_doc(lesson_id: str) -> Dict[str, Any]:
    oid = _validate_object_id(lesson_id)

    doc = await mongo_db.lessons.find_one({"_id": oid})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )
    return doc


async def start_chat(session: AsyncSession, lesson_id: str, user_id: int) -> Dict[str, Any]:
    svc = UserService()
    user = await svc.get_user_by_id(session, user_id)
    if not user:
        raise USER_NOT_FOUND_ERROR

    lesson = await _fetch_lesson_doc(lesson_id)
    ctx = extract_compact_context(lesson)
    system_prompt = build_system_prompt(ctx)

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

    state = {
        "lesson_id": lesson_id,
        "user_id": user_id,
        "chat": [{"role": "assistant", "text": greeting}],
    }

    doc = {
        "lesson_id": lesson_id,
        "user_id": user_id,
        "system_prompt": system_prompt,
        "state": state,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await CHAT_COLLECTION.insert_one(doc)

    return {"session_id": str(result.inserted_id), "message": greeting, "chat": state["chat"]}


async def send_chat_message(session: AsyncSession, session_id: str, text: str) -> Dict[str, Any]:
    oid = _validate_object_id(session_id)

    chat_doc = await CHAT_COLLECTION.find_one({"_id": oid})
    if not chat_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    svc = UserService()
    user = await svc.get_user_by_id(session, chat_doc.get("user_id"))
    if not user:
        raise USER_NOT_FOUND_ERROR

    system_prompt: str = chat_doc.get("system_prompt") or ""
    history: List[Dict[str, str]] = chat_doc.get("state", {}).get("chat", [])

    history.append({"role": "user", "text": text})

    llm_messages = [
        {"role": m.get("role", "user"), "content": m.get("text", "")}
        for m in history[-DEFAULT_HISTORY_LIMIT :]
    ]

    assistant_reply = await chat_client(system_prompt, llm_messages)

    history.append({"role": "assistant", "text": assistant_reply})

    update_data = {
        "state.chat": history,
        "updated_at": datetime.utcnow(),
    }

    await CHAT_COLLECTION.update_one({"_id": oid}, {"$set": update_data})

    return {
        "session_id": session_id,
        "message": assistant_reply,
        "chat": history,
    }
