from io import BytesIO
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config.minio_client_cfg import S3Client
from app.repositories.lesson_file_repository import LessonFilesRepository
from app.schemas.lesson_file import LessonFileCreate


class LessonFilesService:
    """
    Сервис для управления файлами уроков.

    Обрабатывает загрузку и скачивание файлов уроков, 
    сохраняя их в S3 хранилище и создавая записи в базе данных.
    """

    def __init__(self):
        """
        Инициализация сервиса файлов уроков.

        Создает клиент S3 для работы с хранилищем и репозиторий для работы с базой данных.
        """
        self.s3 = S3Client()
        self.repo = LessonFilesRepository()

    async def upload(
        self,
        db: Session,
        file: UploadFile,
        course_slug: str,
        lesson_slug: str,
    ):
        """
        Загрузка файла урока в хранилище.

        Args:
            db: Сессия базы данных
            file: Загружаемый файл
            course_slug: Slug курса
            lesson_slug: Slug урока

        Returns:
            Объект базы данных с информацией о загруженном файле
        """
        content = await file.read()
        size = len(content)
        mime = file.content_type

        key = f"{course_slug}/{lesson_slug}/{file.filename}"

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
        """
        Скачивание файла урока из хранилища.

        Args:
            db: Сессия базы данных
            file_name: Имя файла для скачивания

        Returns:
            Кортеж из объекта базы данных и содержимого файла, 
            или (None, None) если файл не найден
        """
        db_obj = self.repo.get_by_file_name(db, file_name)
        if not db_obj:
            return None, None

        content = self.s3.download_file(db_obj.file_path)
        return db_obj, content


lesson_files_service = LessonFilesService()
