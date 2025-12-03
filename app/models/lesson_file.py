from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Numeric,
    DateTime,
)
from sqlalchemy.sql import func

from app.models.base import Base

class LessonFile(Base):
    __tablename__ = "lessons_files"

    id = Column(BigInteger, primary_key=True, index=True)
    file_name = Column(String(256), nullable=True)
    file_path = Column(String(256), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(256), nullable=True)
    state = Column(Numeric(1), nullable=False, server_default="1")
    lesson_id = Column(String(64), index=True, nullable=True)
    unit_id = Column(String(64), nullable=True)
    activity_id = Column(String(64), nullable=True)
    media_type = Column(String(16), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
