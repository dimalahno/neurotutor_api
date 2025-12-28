from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db_cfg import get_db
from app.core.deps import get_session
from app.schemas.voice_chat import VoiceStartResponse, VoiceStartRequest, VoiceStopResponse, VoiceStopRequest, \
    VoiceOfferResponse, VoiceOfferRequest
from app.services.voice_chat_service import (
    start_voice_chat,
    create_call_from_offer,
    stop_voice_chat,
)

router = APIRouter(prefix="/voice", tags=["voice"])

@router.post("/start", response_model=VoiceStartResponse)
async def voice_start(payload: VoiceStartRequest,
                      session: AsyncSession = Depends(get_session)):
    return await start_voice_chat(
        session,
        lesson_id=payload.lesson_id,
        user_id=payload.user_id,
        voice=payload.voice,
        model=payload.model,
    )


@router.post("/webrtc/offer", response_model=VoiceOfferResponse)
async def voice_webrtc_offer(payload: VoiceOfferRequest,
                             session: AsyncSession = Depends(get_session)):
    return await create_call_from_offer(
        session,
        session_id=payload.session_id,
        user_id=payload.user_id,
        sdp_offer=payload.sdp_offer,
    )


@router.post("/stop", response_model=VoiceStopResponse)
async def voice_stop(payload: VoiceStopRequest,
                     session: AsyncSession = Depends(get_session)):
    return await stop_voice_chat(
        session,
        session_id=payload.session_id,
        user_id=payload.user_id,
    )
