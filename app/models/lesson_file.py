from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func

from app.models.base import Base

class LessonFile(Base):
    __tablename__ = "lessons_files"

    id = Column(BigInteger, primary_key=True, index=True)
    file_name = Column(String(256))
    file_path = Column(String(256))
    file_size = Column(BigInteger)
    mime_type = Column(String(256))

    course_slug = Column(String(64), index=True)
    lesson_slug = Column(String(64), index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
