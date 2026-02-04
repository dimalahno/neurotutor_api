import logging
from typing import Dict, List, Optional

import httpx
from fastapi import HTTPException
from starlette import status

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434".rstrip("/")
OLLAMA_MODEL = "qwen2.5:7b-instruct"
OLLAMA_TIMEOUT_S = 300.0  # ! было 60.0, увеличили read-timeout (модель может отвечать дольше)


def _normalize_messages(system_prompt: Optional[str], messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    if system_prompt:
        out.append({"role": "system", "content": system_prompt})

    for m in messages or []:
        role = (m.get("role") or "user").lower()
        if role not in ("system", "user", "assistant"):
            role = "user"
        content = (m.get("content") or "").strip()
        if content:
            out.append({"role": role, "content": content})
    return out


def _build_check_text_input(text: str, scoring_dimensions: List[str]) -> str:
    dims = "\n- " + "\n- ".join(scoring_dimensions) if scoring_dimensions else ""
    return f"Student text:\n{text}\n\nScoring dimensions:{dims}"

async def local_chat_client(
    system_prompt: str,
    messages: List[Dict[str, str]],
    *,
    temperature: float = 0.6,
    max_output_tokens: int = 300,
) -> str:
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": _normalize_messages(system_prompt, messages),
        "stream": False,
        "options": {
            "temperature": float(temperature),
            "num_predict": int(max_output_tokens),
        },
    }

    # ! Раздельные таймауты: read может быть долгим из-за генерации токенов
    timeout = httpx.Timeout(
        connect=10.0,
        read=OLLAMA_TIMEOUT_S,
        write=10.0,
        pool=10.0,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            resp.raise_for_status()
            data = resp.json()

        text = (((data or {}).get("message") or {}).get("content") or "").strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Ollama returned empty response",
            )
        return text
    
    except httpx.ReadTimeout:
        # Превышено время ожидания ответа от Ollama.
        logger.exception("Ollama read timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Ollama timeout (read>{OLLAMA_TIMEOUT_S}s). Increase OLLAMA_TIMEOUT_S or reduce max_output_tokens.",
        )

    except httpx.HTTPStatusError as e:
        logger.exception("Ollama HTTP error")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama HTTP {e.response.status_code}: {e.response.text}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Ollama chat failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama error: {e}",
        )


async def local_check_text(
    text: str,
    system_prompt: str,
    scoring_dimensions: List[str],
    *,
    temperature: float = 0.2,
    max_output_tokens: int = 300,
) -> str:
    user_text = _build_check_text_input(text, scoring_dimensions)
    return await local_chat_client(
        system_prompt or "You are an English teacher. Give short feedback.",
        [{"role": "user", "content": user_text}],
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )