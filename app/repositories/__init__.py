from sqlalchemy.orm import Session
from app.models import Course
from app.models import Enrollment
from app.models import UserProgress

# Courses
class CourseRepository:
    @staticmethod
    def create(db: Session, course_data: Course):
        db.add(course_data)
        db.commit()
        db.refresh(course_data)
        return course_data

    @staticmethod
    def list(db: Session):
        return db.query(Course).all()


# Enrollments
class EnrollmentRepository:
    @staticmethod
    def create(db: Session, enrollment_data: Enrollment):
        db.add(enrollment_data)
        db.commit()
        db.refresh(enrollment_data)
        return enrollment_data

    @staticmethod
    def list_by_user(db: Session, user_id: int):
        return db.query(Enrollment).filter(Enrollment.user_id == user_id).all()


# User Progress
class UserProgressRepository:
    @staticmethod
    def create(db: Session, progress_data: UserProgress):
        db.add(progress_data)
        db.commit()
        db.refresh(progress_data)
        return progress_data

    @staticmethod
    def list_by_enrollment(db: Session, enrollment_id: int):
        return db.query(UserProgress).filter(UserProgress.enrollment_id == enrollment_id).all()

