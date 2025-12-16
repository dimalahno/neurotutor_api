import os
import tempfile
from openai import AsyncOpenAI
from fastapi import UploadFile, HTTPException
from app.config.main_cfg import settings
from app.schemas.audio_check import AudioCheckMeta

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def transcribe_audio(file: UploadFile) -> str:
    suffix = os.path.splitext(file.filename or "")[1] or ".webm"
    tmp_path = None

    try:
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)

        content = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(content)

        with open(tmp_path, "rb") as audio:
            result = await client.audio.transcriptions.create(
                file=audio,
                model="gpt-4o-transcribe",
                language="en",
            )

        return (result.text or "").strip()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ASR failed: {e}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _build_audio_input(meta: AudioCheckMeta, transcript: str) -> str:
    return (
        f"Student transcript:\n{transcript}\n\n"
        f"Model answer:\n{meta.modelAnswer}\n\n"
        f"Target patterns:\n- " + "\n- ".join(meta.targetPatterns) + "\n\n"
        f"Keywords:\n- " + "\n- ".join(meta.keywords) + "\n\n"
        f"Scoring dimensions:\n- " + "\n- ".join(meta.scoringDimensions) + "\n"
    )

async def transcribe_and_score(file: UploadFile, meta: AudioCheckMeta) -> dict:
    suffix = os.path.splitext(file.filename or "")[1] or ".webm"
    tmp_path = None

    try:
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)

        content = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(content)

        # 1) ASR
        with open(tmp_path, "rb") as audio:
            asr = await client.audio.transcriptions.create(
                file=audio,
                model="gpt-4o-transcribe",
                language=meta.language or "en",
            )
        transcript = (asr.text or "").strip()

        # 2) LLM evaluation (mini)
        eval_resp = await client.responses.create(
            model="gpt-4.1-mini",
            instructions=meta.systemPrompt,
            input=_build_audio_input(meta, transcript),
            temperature=0.2,
            max_output_tokens=220,
        )

        return {
            "status": "ok",
            "transcription": transcript,
            "message": eval_resp.output_text,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ASR/Scoring failed: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

def _build_text_input(text: str, scoring_dimensions: list[str]) -> str:
    dims = "\n- " + "\n- ".join(scoring_dimensions) if scoring_dimensions else ""
    return f"Student text:\n{text}\n\nScoring dimensions:{dims}"

async def check_text(text: str, system_prompt: str, scoring_dimensions: list[str]) -> str:
    resp = await client.responses.create(
        model="gpt-4.1-mini",
        instructions=system_prompt or "You are an English teacher. Give short feedback.",
        input=_build_text_input(text, scoring_dimensions),
        temperature=0.2,
        max_output_tokens=220,
    )
    return resp.output_text.strip()
