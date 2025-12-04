from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.lesson_file import LessonFile
from app.schemas.lesson_file import LessonFileCreate


class LessonFilesRepository:

    def get_by_file_name(self, db: Session, file_name: str) -> Optional[LessonFile]:
        return (
            db.query(LessonFile)
              .filter(LessonFile.file_name == file_name)
              .first()
        )

    def list_by_lesson(self, db: Session, course_slug: str, lesson_slug: str) -> List[LessonFile]:
        return (
            db.query(LessonFile)
              .filter(
                  LessonFile.course_slug == course_slug,
                  LessonFile.lesson_slug == lesson_slug
              )
              .all()
        )

    def create(self, db: Session, obj_in: LessonFileCreate) -> LessonFile:
        db_obj = LessonFile(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: LessonFile):
        db.delete(db_obj)
        db.commit()
