from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LessonFileBase(BaseModel):
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

    course_slug: Optional[str] = None
    lesson_slug: Optional[str] = None


class LessonFileCreate(LessonFileBase):
    file_name: str
    file_path: str
    course_slug: str
    lesson_slug: str


class LessonFileUpdate(BaseModel):
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    course_slug: Optional[str] = None
    lesson_slug: Optional[str] = None


class LessonFileInDB(BaseModel):
    id: int
    file_name: str
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    course_slug: Optional[str]
    lesson_slug: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LessonFile(LessonFileInDB):
    pass