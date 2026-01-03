import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException
from starlette import status

from app.config.main_cfg import settings

logger = logging.getLogger(__name__)

OPENAI_BASE_URL = "https://api.openai.com/v1"

DEFAULT_REALTIME_MODEL = "gpt-realtime-mini"

DEFAULT_VOICE = "marin"

@dataclass
class RealtimeCallResult:
    call_id: str
    sdp_answer: str
    location: Optional[str] = None


def _extract_call_id(location_header: Optional[str]) -> str:
    if not location_header:
        return ""

    path = urlparse(location_header).path  # работает и для полного URL, и для "/v1/..."
    last = path.rstrip("/").rsplit("/", 1)[-1]

    logger.info("Extracted call id: %s", last)

    # last должен быть реальным id, а не "calls"
    if not last or last == "calls":
        return ""

    return last


def build_realtime_session_config(
    *,
    instructions: str,
    model: str = DEFAULT_REALTIME_MODEL,
    voice: str = DEFAULT_VOICE,
    max_output_tokens: int | str = "inf",
) -> Dict[str, Any]:
    return {
        "type": "realtime",
        "model": model,
        "instructions": instructions or "",
        "max_output_tokens": max_output_tokens,
        "output_modalities": ["audio"],
        "audio": {
            "input": {
                "noise_reduction": {"type": "near_field"},
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500,
                    "create_response": True,
                    "interrupt_response": False,
                },
            },
            "output": {
                "voice": voice,
            },
        },
    }


async def create_webrtc_call(*, sdp_offer: str, session_config: Dict[str, Any]) -> RealtimeCallResult:
    if not sdp_offer or not sdp_offer.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SDP offer is empty")

    url = f"{OPENAI_BASE_URL}/realtime/calls"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}

    # ВАЖНО: поле sdp должно быть form field без filename (None, ...)
    # Аналогично session: строка JSON, тоже без filename
    files = {
        "sdp": (None, sdp_offer, "application/sdp"),
        "session": (None, json.dumps(session_config), "application/json"),
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, files=files)

        if resp.status_code != 201:
            logger.error("Realtime create call failed: %s %s", resp.status_code, resp.text)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Realtime create call failed: {resp.status_code}: {resp.text}",
            )

        location = resp.headers.get("Location")
        call_id = _extract_call_id(location)

        logger.info("create_webrtc_call Realtime create call: %s", call_id)

        if not call_id:
            logger.error("Realtime create call: invalid Location header: %r", location)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Realtime create call failed: invalid Location header (no call_id)",
            )

        return RealtimeCallResult(call_id=call_id, sdp_answer=resp.text, location=location)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Realtime create call error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Realtime error: {e}")


def normalize_call_id(raw: Optional[str]) -> str:
    if not raw:
        return ""
    raw = raw.strip().rstrip("/")

    # если прислали URL или path — берём последний сегмент
    if "/" in raw:
        raw = raw.rsplit("/", 1)[-1]

    # отсечь очевидный мусор
    if raw in {"calls", "call", "realtime", "v1", "hangup"}:
        return ""

    return raw


async def hangup_call(call_id: str) -> None:
    call_id = normalize_call_id(call_id)

    logger.info("hangup_call Realtime hangup: %s", call_id)

    if not call_id:
        return

    url = f"{OPENAI_BASE_URL}/realtime/calls/{call_id}/hangup"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, headers=headers)

    if resp.status_code == 404:
        logger.warning("Realtime hangup: call not found (already ended?) call_id=%s", call_id)
        return

    if resp.status_code != 200:
        logger.error("Realtime hangup failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Realtime hangup failed: {resp.status_code}",
        )
