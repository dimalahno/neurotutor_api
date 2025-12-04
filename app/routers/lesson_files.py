from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config.db_cfg import get_db
from app.schemas.lesson_file import LessonFile
from app.services.lesson_files_service import lesson_files_service

router = APIRouter(
    prefix="/lessons-files",
    tags=["lessons_files"],
)

@router.post("/upload", response_model=LessonFile)
async def upload_file(
    file: UploadFile = File(...),
    course_slug: str = Form(...),
    lesson_slug: str = Form(...),
    db: Session = Depends(get_db),
):
    obj = await lesson_files_service.upload(
        db=db,
        file=file,
        course_slug=course_slug,
        lesson_slug=lesson_slug,
    )
    return obj


@router.get("/{file_name}")
def download_file(
    file_name: str,
    db: Session = Depends(get_db)
):
    db_obj, content = lesson_files_service.download(db, file_name)
    if not db_obj:
        raise HTTPException(status_code=404, detail="File not found")

    media_type = db_obj.mime_type

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{db_obj.file_name}"'
        },
    )
