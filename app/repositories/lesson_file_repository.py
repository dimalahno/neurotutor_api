from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.lesson_file import LessonFile
from app.schemas.lesson_file import LessonFileCreate, LessonFileUpdate


class LessonFilesRepository:
    def get(self, db: Session, lesson_file_id: int) -> Optional[LessonFile]:
        return (
            db.query(LessonFile)
            .filter(LessonFile.id == lesson_file_id)
            .first()
        )

    def list_by_lesson(
        self,
        db: Session,
        lesson_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LessonFile]:
        return (
            db.query(LessonFile)
            .filter(LessonFile.lesson_id == lesson_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, db: Session, obj_in: LessonFileCreate) -> LessonFile:
        obj_data = obj_in.model_dump()
        db_obj = LessonFile(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        db_obj: LessonFile,
        obj_in: LessonFileUpdate,
    ) -> LessonFile:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: LessonFile) -> None:
        db.delete(db_obj)
        db.commit()
