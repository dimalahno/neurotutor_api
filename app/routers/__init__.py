from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Course, Enrollment, UserProgress
from ..repositories import CourseRepository, EnrollmentRepository, UserProgressRepository

router = APIRouter()

# Courses
@router.post("/courses", response_model=dict)
def create_course(title: str, description: str = "", db: Session = Depends(get_db)):
    course = Course(title=title, description=description)
    CourseRepository.create(db, course)
    return {"id": course.id, "title": course.title, "description": course.description}


@router.get("/courses", response_model=list)
def list_courses(db: Session = Depends(get_db)):
    courses = CourseRepository.list(db)
    return [{"id": c.id, "title": c.title, "description": c.description} for c in courses]


# Enrollments
@router.post("/enrollments", response_model=dict)
def create_enrollment(user_id: int, course_id: int, db: Session = Depends(get_db)):
    enrollment = Enrollment(user_id=user_id, course_id=course_id)
    EnrollmentRepository.create(db, enrollment)
    return {"id": enrollment.id, "user_id": enrollment.user_id, "course_id": enrollment.course_id}


# User Progress
@router.post("/progress", response_model=dict)
def create_progress(enrollment_id: int, completed_lessons: int = 0, score: float = 0.0, db: Session = Depends(get_db)):
    progress = UserProgress(enrollment_id=enrollment_id, completed_lessons=completed_lessons, score=score)
    UserProgressRepository.create(db, progress)
    return {"id": progress.id, "enrollment_id": progress.enrollment_id, "completed_lessons": progress.completed_lessons, "score": progress.score}
