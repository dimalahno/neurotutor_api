from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .database import get_db
from .models import Base, engine, Course, Enrollment, UserProgress
from .schemas import CourseCreate, CourseOut, EnrollmentCreate, EnrollmentOut, UserProgressCreate, UserProgressOut
from .repositories import CourseRepository, EnrollmentRepository, UserProgressRepository

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NeuroTutor API - Courses, Enrollments, Progress")

# Courses
@app.post("/courses", response_model=CourseOut)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    course_obj = Course(title=course.title, description=course.description)
    return CourseRepository.create(db, course_obj)

@app.get("/courses", response_model=List[CourseOut])
def list_courses(db: Session = Depends(get_db)):
    return CourseRepository.list(db)


# Enrollments
@app.post("/enrollments", response_model=EnrollmentOut)
def create_enrollment(enrollment: EnrollmentCreate, db: Session = Depends(get_db)):
    enrollment_obj = Enrollment(user_id=enrollment.user_id, course_id=enrollment.course_id)
    return EnrollmentRepository.create(db, enrollment_obj)

@app.get("/enrollments/user/{user_id}", response_model=List[EnrollmentOut])
def list_enrollments(user_id: int, db: Session = Depends(get_db)):
    return EnrollmentRepository.list_by_user(db, user_id)


# User Progress
@app.post("/progress", response_model=UserProgressOut)
def create_progress(progress: UserProgressCreate, db: Session = Depends(get_db)):
    progress_obj = UserProgress(
        enrollment_id=progress.enrollment_id,
        lesson_id=progress.lesson_id,
        completed=progress.completed,
        score=progress.score
    )
    return UserProgressRepository.create(db, progress_obj)

@app.get("/progress/enrollment/{enrollment_id}", response_model=List[UserProgressOut])
def list_progress(enrollment_id: int, db: Session = Depends(get_db)):
    return UserProgressRepository.list_by_enrollment(db, enrollment_id)
