import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.mongo_cfg import mongo_db
from app.config.db_cfg import get_async_session
from app.repositories.course_repository import CourseRepository

router = APIRouter(prefix="/admin/content", tags=["admin-content"],)


async def _read_json_file(file: UploadFile) -> Any:
    raw = await file.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file",
        )


@router.post("/upload-courses")
async def upload_courses(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
):
    """
    1) Загружаем JSON с курсами (например init_courses.json)
    2) Сохраняем/апдейтим документы в MongoDB (коллекция courses)
    3) Сохраняем/апдейтим строки в Postgres (таблица courses)
    """
    course_data = await _read_json_file(file)

    if not isinstance(course_data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON must be a single object",
        )

    title = course_data.get("title") or ""
    description = course_data.get("description") or ""
    level = course_data.get("lang_level")
    slug = course_data.get("slug")

    if not slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course must contain 'slug'",
        )

    courses_coll = mongo_db["courses"]

    # Пытаемся найти курс по slug
    existing = await courses_coll.find_one({"slug": slug})
    # 1) Mongo: сохраняем в коллекцию courses
    if existing:
        # Используем существующий _id из Mongo
        mongo_course_id = str(existing["_id"])
        await courses_coll.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "slug": slug,
                    "title": title,
                    "description": description,
                    "level": level,
                    "lessons": []
                }
            },
        )
    else:
        # Даём Mongo самому сгенерировать _id
        insert_result = await courses_coll.insert_one(
            {
                "slug": slug,
                "title": title,
                "description": description,
                "level": level,
                "lessons": []
            }
        )
        mongo_course_id = str(insert_result.inserted_id)



    # 2) Postgres: upsert по mongo_course_id
    course_row = await CourseRepository.upsert_by_mongo_id(
        session=session,
        mongo_course_id=mongo_course_id,
        title=title,
        description=description,
        level=level,
    )

    await session.commit()
    return {
        "status": "ok",
        "count": 1,
        "courses": [
            {
                "mongo_course_id": mongo_course_id,
                "pg_course_id": course_row.id,
            }
        ],
    }


@router.post("/upload-lessons")
async def upload_lessons(
    file: UploadFile = File(...),
):
    """
    1) Загружаем JSON с уроками (например init_lessons.json)
    2) Сохраняем/апдейтим документы в MongoDB (коллекция lessons)
    3) Обновляем первый найденный курс в Mongo, заполняя поле lessons[]:
       [{lesson_id, index, title}, ...]
    """
    data = await _read_json_file(file)

    if isinstance(data, dict):
        lessons_data = [data]
    elif isinstance(data, list):
        lessons_data = data
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON must be object or array of objects",
        )

    lessons_meta: List[Dict[str, Any]] = []

    for idx, lesson_doc in enumerate(lessons_data, start=1):
        lesson_id: Optional[str] = (
            lesson_doc.get("_id")
            or lesson_doc.get("lesson_id")
            or lesson_doc.get("id")
        )
        if not lesson_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lesson must contain '_id' or 'lesson_id'",
            )

        lesson_doc["_id"] = lesson_id
        index = lesson_doc.get("index", idx)
        title = lesson_doc.get("title", "")

        # Mongo: сохраняем/обновляем документ урока
        await mongo_db["lessons"].replace_one(
            {"_id": lesson_id},
            lesson_doc,
            upsert=True,
        )

        lessons_meta.append(
            {
                "lesson_id": lesson_id,
                "index": index,
                "title": title,
            }
        )

    # Привязываем все уроки к первому курсу (MVP-вариант под текущий init_courses.json)
    course_doc = await mongo_db["courses"].find_one({})
    linked_course_id = None
    if course_doc:
        linked_course_id = course_doc["_id"]
        await mongo_db["courses"].update_one(
            {"_id": linked_course_id},
            {"$set": {"lessons": lessons_meta}},
        )

    return {
        "status": "ok",
        "lessons_count": len(lessons_meta),
        "linked_course_id": linked_course_id,
    }
