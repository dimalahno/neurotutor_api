from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class CourseBase(BaseModel):
    mongo_course_id: str
    title: str
    description: str
    level: Optional[str] = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    level: Optional[str] = None


class CourseRead(CourseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
