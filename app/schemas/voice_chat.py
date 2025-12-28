from pydantic import BaseModel, Field


class VoiceStopRequest(BaseModel):
    session_id: str
    user_id: int = Field(..., gt=0)


class VoiceStopResponse(BaseModel):
    session_id: str
    status: str

class VoiceStartRequest(BaseModel):
    lesson_id: str = Field(..., min_length=10)
    user_id: int = Field(..., gt=0)
    # опционально: дать возможность выбирать голос/модель на старте
    voice: str | None = None
    model: str | None = None


class VoiceStartResponse(BaseModel):
    session_id: str
    greeting: str
    status: str


class VoiceOfferRequest(BaseModel):
    session_id: str
    user_id: int = Field(..., gt=0)
    sdp_offer: str = Field(..., min_length=10)


class VoiceOfferResponse(BaseModel):
    session_id: str
    call_id: str
    sdp_answer: str
    status: str