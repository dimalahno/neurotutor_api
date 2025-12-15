from pydantic import BaseModel
from typing import List, Optional

class AudioCheckMeta(BaseModel):
    modelAnswer: str
    targetPatterns: List[str] = []
    keywords: List[str] = []
    systemPrompt: str
    scoringDimensions: List[str] = []
    language: Optional[str] = "en"
