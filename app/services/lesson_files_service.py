from io import BytesIO
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config.minio_client_cfg import S3Client
from app.repositories.lesson_file_repository import LessonFilesRepository
from app.schemas.lesson_file import LessonFileCreate


class LessonFilesService:

    def __init__(self):
        self.s3 = S3Client()
        self.repo = LessonFilesRepository()

    async def upload(
        self,
        db: Session,
        file: UploadFile,
        course_slug: str,
        lesson_slug: str,
    ):
        content = await file.read()
        size = len(content)
        mime = file.content_type

        key = file.filename  # MVP — имя файла как ключ

        db_obj = self.repo.create(
            db,
            LessonFileCreate(
                file_name=file.filename,
                file_path=key,
                file_size=size,
                mime_type=mime,
                course_slug=course_slug,
                lesson_slug=lesson_slug,
            )
        )

        self.s3.upload_file(
            file_obj=BytesIO(content),
            key=key,
            content_type=mime,
        )

        return db_obj

    def download(self, db: Session, file_name: str):
        db_obj = self.repo.get_by_file_name(db, file_name)
        if not db_obj:
            return None, None

        content = self.s3.download_file(db_obj.file_path)
        return db_obj, content


lesson_files_service = LessonFilesService()
