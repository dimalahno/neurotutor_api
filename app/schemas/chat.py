from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    text: str = Field(..., min_length=1, description="User message text")
