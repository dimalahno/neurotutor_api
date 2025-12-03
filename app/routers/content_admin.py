import json
from typing import Any, Dict, List, Optional

from bson import ObjectId
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


@router.post("/upload-lessons/{course_id}")
async def upload_lessons(
    course_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
):
    """
    1) Загружаем JSON с одним уроком (dict)
    2) Находим курс по course_id в Postgres
    3) Берём mongo_course_id из курса
    4) Создаём lesson в Mongo (id генерит Mongo)
    5) В lesson пишем mongo_course_id для связки
    6) Добавляем lesson в lessons[] у соответствующего course (Mongo)
    """
    data = await _read_json_file(file)

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON must be a single object",
        )

    # Ищем курс в Postgres по course_id
    course_row = await CourseRepository.get_by_id(session, course_id)
    if not course_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    mongo_course_id = course_row.mongo_course_id
    if not mongo_course_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Course has no mongo_course_id",
        )

    # Конвертируем строковый идентификатор в ObjectId для Mongo
    try:
        course_mongo_obj_id = ObjectId(mongo_course_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid mongo_course_id stored for course",
        )

    lessons_coll = mongo_db["lessons"]
    courses_coll = mongo_db["courses"]

    index = data.get("index", 1)
    title = data.get("title", "")

    # Готовим документ урока: _id не берём из файла, mongo_course_id добавляем
    lesson_doc: Dict[str, Any] = dict(data)
    lesson_doc["mongo_course_id"] = mongo_course_id

    # Вставляем урок, _id генерит Mongo
    insert_result = await lessons_coll.insert_one(lesson_doc)
    lesson_mongo_id = str(insert_result.inserted_id)

    # Метаданные для встраивания в course.lessons[]
    lesson_meta = {
        "lesson_id": lesson_mongo_id,
        "index": index,
        "title": title,
    }

    # Проверяем, что курс есть в Mongo
    course_doc = await courses_coll.find_one({"_id": course_mongo_obj_id})
    if not course_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found in MongoDB",
        )

    # Добавляем lesson в массив lessons курса
    await courses_coll.update_one(
        {"_id": course_mongo_obj_id},
        {"$push": {"lessons": lesson_meta}},
    )

    return {
        "status": "ok",
        "lesson_id": lesson_mongo_id,
        "course_id": course_id,
        "mongo_course_id": mongo_course_id,
    }

@router.post("/update-lesson/{course_id}/{lesson_id}")
async def update_lesson(
    course_id: str,
    lesson_id: str,
    file: UploadFile = File(...)
):
    """
    Обновление урока в MongoDB:
    1) Проверяем курс по course_id
    2) Проверяем урок по lesson_id
    3) Обновляем документ урока целиком ($set)
    4) Обновляем метаданные урока в courses.lessons[]
    """
    data = await _read_json_file(file)
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400,
            detail="JSON must be a single object",
        )

    lessons_coll = mongo_db["lessons"]
    courses_coll = mongo_db["courses"]

    # Validate ObjectId
    try:
        course_obj_id = ObjectId(course_id)
        lesson_obj_id = ObjectId(lesson_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid Mongo ObjectId")

    # --- Проверяем курс ---
    course_doc = await courses_coll.find_one({"_id": course_obj_id})
    if not course_doc:
        raise HTTPException(status_code=404, detail="Course not found")

    # --- Проверяем урок ---
    lesson_doc = await lessons_coll.find_one({"_id": lesson_obj_id})
    if not lesson_doc:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # --- Обновляем lesson ---
    # Обязательно перезаписываем mongo_course_id для целостности
    data["mongo_course_id"] = course_id

    await lessons_coll.update_one(
        {"_id": lesson_obj_id},
        {"$set": data}
    )

    # --- Обновляем метаданные в courses.lessons[] ---
    index = data.get("index")
    title = data.get("title")

    # Обновить объект в массиве lessons курса
    await courses_coll.update_one(
        {"_id": course_obj_id, "lessons.lesson_id": lesson_id},
        {
            "$set": {
                "lessons.$.index": index,
                "lessons.$.title": title,
            }
        }
    )

    return {
        "status": "ok",
        "lesson_id": lesson_id,
        "course_id": course_id,
        "updated_fields": ["lesson document", "course.lessons[] metadata"]
    }
