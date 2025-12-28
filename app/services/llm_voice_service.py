import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException
from starlette import status

from app.config.main_cfg import settings

logger = logging.getLogger(__name__)

OPENAI_BASE_URL = "https://api.openai.com/v1"

# из официальных примеров Realtime API :contentReference[oaicite:6]{index=6}
DEFAULT_REALTIME_MODEL = "gpt-realtime"

# пример из WebRTC guide :contentReference[oaicite:7]{index=7}
DEFAULT_VOICE = "marin"


@dataclass
class RealtimeCallResult:
    call_id: str
    sdp_answer: str
    location: Optional[str] = None


def _extract_call_id(location_header: Optional[str]) -> str:
    if not location_header:
        return ""
    # Location обычно вида /v1/realtime/calls/<call_id>
    m = re.search(r"/realtime/calls/([^/?]+)", location_header)
    return m.group(1) if m else ""


def build_realtime_session_config(
    *,
    instructions: str,
    model: str = DEFAULT_REALTIME_MODEL,
    voice: str = DEFAULT_VOICE,
    max_output_tokens: int | str = 300,
) -> Dict[str, Any]:
    # "session" использует те же параметры что create client secret :contentReference[oaicite:8]{index=8}
    return {
        "type": "realtime",
        "model": model,
        "instructions": instructions or "",
        "max_output_tokens": max_output_tokens,
        "output_modalities": ["audio"],
        "audio": {
            "output": {
                "voice": voice,
            }
        },
    }


async def create_webrtc_call(*, sdp_offer: str, session_config: Dict[str, Any]) -> RealtimeCallResult:
    if not sdp_offer or not sdp_offer.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SDP offer is empty")

    url = f"{OPENAI_BASE_URL}/realtime/calls"  # :contentReference[oaicite:9]{index=9}
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}

    # multipart form: sdp as application/sdp, session as application/json :contentReference[oaicite:10]{index=10}
    files = [
        ("sdp", ("offer.sdp", sdp_offer, "application/sdp")),
        ("session", ("session.json", json.dumps(session_config), "application/json")),
    ]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, files=files)

        if resp.status_code != 201:
            logger.error("Realtime create call failed: %s %s", resp.status_code, resp.text)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Realtime create call failed: {resp.status_code}",
            )

        location = resp.headers.get("Location")
        call_id = _extract_call_id(location)
        if not call_id:
            # По докам Location должен быть, но если нет — всё равно вернём ответ SDP,
            # а call_id пустой будет сигналом для логов/диагностики.
            logger.warning("Realtime create call: missing/unknown Location header: %s", location)

        return RealtimeCallResult(call_id=call_id, sdp_answer=resp.text, location=location)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Realtime create call error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Realtime error: {e}")


async def hangup_call(call_id: str) -> None:
    if not call_id:
        return

    url = f"{OPENAI_BASE_URL}/realtime/calls/{call_id}/hangup"  # :contentReference[oaicite:11]{index=11}
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers)

        if resp.status_code != 200:
            logger.error("Realtime hangup failed: %s %s", resp.status_code, resp.text)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Realtime hangup failed: {resp.status_code}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Realtime hangup error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Realtime error: {e}")
