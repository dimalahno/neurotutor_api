from pydantic import BaseModel
from typing import List

class TextCheckRequest(BaseModel):
    text: str
    systemPrompt: str = ""
    scoringDimensions: List[str] = []

class TextCheckResponse(BaseModel):
    status: str
    message: str
