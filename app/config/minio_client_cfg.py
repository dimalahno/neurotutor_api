import boto3
from botocore.client import Config
from typing import BinaryIO

from app.config.main_cfg import settings

"""Класс для работы с S3-совместимым хранилищем (MinIO).
Предоставляет базовые операции для работы с файлами."""


class S3Client:
    """Инициализация клиента S3.
    Создает подключение к хранилищу и проверяет наличие бакета."""

    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name=settings.MINIO_REGION,
            config=Config(signature_version="s3v4")
        )
        self.bucket = settings.MINIO_BUCKET

        # Автоматическое создание бакета
        self.ensure_bucket()

    """Загрузка файла в хранилище.

    Args:
        file_obj: Бинарный объект файла
        key: Ключ файла в хранилище
        content_type: MIME-тип файла
    """

    def upload_file(self, file_obj: BinaryIO, key: str, content_type: str = "application/octet-stream"):
        self.s3.upload_fileobj(
            Fileobj=file_obj,
            Bucket=self.bucket,
            Key=key,
            ExtraArgs={"ContentType": content_type}
        )

    """Скачивание файла из хранилища.

    Args:
        key: Ключ файла в хранилище
    Returns:
        bytes: Содержимое файла в бинарном виде
    """

    def download_file(self, key: str) -> bytes:
        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    """Удаление файла из хранилища.

    Args:
        key: Ключ файла в хранилище
    """

    def delete_file(self, key: str):
        self.s3.delete_object(Bucket=self.bucket, Key=key)

    """Проверка существования файла в хранилище.

    Args:
        key: Ключ файла в хранилище
    Returns:
        bool: True если файл существует, False если нет
    """

    def file_exists(self, key: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except self.s3.exceptions.ClientError:
            return False

    """Проверка существования и создание бакета при необходимости."""

    def ensure_bucket(self):
        # Получаем список существующих бакетов
        buckets = [b["Name"] for b in self.s3.list_buckets().get("Buckets", [])]

        # Если бакета нет — создаем
        if self.bucket not in buckets:
            self.s3.create_bucket(Bucket=self.bucket)