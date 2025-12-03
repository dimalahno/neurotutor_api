from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class LessonFileBase(BaseModel):
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    state: Optional[int] = 1
    lesson_id: Optional[str] = None
    unit_id: Optional[str] = None
    activity_id: Optional[str] = None
    media_type: Optional[str] = None


class LessonFileCreate(LessonFileBase):
    file_name: str
    file_path: str
    media_type: str
    lesson_id: str


class LessonFileUpdate(BaseModel):
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    state: Optional[int] = None
    lesson_id: Optional[str] = None
    unit_id: Optional[str] = None
    activity_id: Optional[str] = None
    media_type: Optional[str] = None


class LessonFileInDBBase(LessonFileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (аналог orm_mode=True)


class LessonFile(LessonFileInDBBase):
    pass


class LessonFileInDB(LessonFileInDBBase):
    pass
