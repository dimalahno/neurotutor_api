import json

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.schemas.audio_check import AudioCheckMeta
from app.schemas.text_check import TextCheckResponse, TextCheckRequest
from app.services.llm_service import transcribe_audio, check_text
from app.services.llm_service import transcribe_and_score

router = APIRouter(prefix="/task", tags=["task"])


@router.post("/transcribe_audio")
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid audio file")

    text = await transcribe_audio(file)
    return {
        "status": "ok",
        "message": text,
    }


@router.post("/check_audio")
async def check_audio_endpoint(
    file: UploadFile = File(...),
    meta: str = Form(...),
):
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid audio file")

    try:
        meta_obj = AudioCheckMeta.model_validate(json.loads(meta))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid meta JSON: {e}")

    return await transcribe_and_score(file, meta_obj)

@router.post("/check_text", response_model=TextCheckResponse)
async def check_text_endpoint(payload: TextCheckRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")

    feedback = await check_text(
        text=payload.text,
        system_prompt=payload.systemPrompt,
        scoring_dimensions=payload.scoringDimensions,
    )
    return TextCheckResponse(status="ok", message=feedback)