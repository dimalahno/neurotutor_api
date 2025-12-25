from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    session_id: str = Field(..., min_length=1, description="Session ID")
    text: str = Field(..., min_length=1, description="User message text")

class ChatStart(BaseModel):
    lesson_id: str = Field(..., min_length=1, description="Lesson ID")
    user_id: int = Field(..., description="User ID")
