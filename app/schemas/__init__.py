from pydantic import BaseModel
from typing import Optional

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = ""

class CourseOut(CourseCreate):
    id: int

class EnrollmentCreate(BaseModel):
    user_id: int
    course_id: int

class EnrollmentOut(EnrollmentCreate):
    id: int

class UserProgressCreate(BaseModel):
    enrollment_id: int
    lesson_id: str
    completed: int = 0
    score: float = 0

class UserProgressOut(UserProgressCreate):
    id: int
