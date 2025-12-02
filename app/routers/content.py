from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder

from app.config.mongo_cfg import mongo_db

router = APIRouter(prefix="/content", tags=["content"], )


@router.get("/courses")
async def list_courses() -> List[Dict[str, Any]]:
    cursor = mongo_db["courses"].find({})
    courses = await cursor.to_list(length=1000)
    return jsonable_encoder(courses, custom_encoder={ObjectId: str})


@router.get("/courses/{course_id}")
async def get_course(course_id: str) -> Dict[str, Any]:
    # Конвертация str → ObjectId
    try:
        oid = ObjectId(course_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ObjectId format",
        )

    course = await mongo_db["courses"].find_one({"_id": oid})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    return jsonable_encoder(course, custom_encoder={ObjectId: str})


@router.get("/lessons")
async def list_lessons() -> List[Dict[str, Any]]:
    cursor = mongo_db["lessons"].find({})
    lessons = await cursor.to_list(length=1000)
    return jsonable_encoder(lessons, custom_encoder={ObjectId: str})


@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: str) -> Dict[str, Any]:
    # Конвертация str → ObjectId
    try:
        oid = ObjectId(lesson_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ObjectId format",
        )

    lesson = await mongo_db["lessons"].find_one({"_id": oid})
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )
    return jsonable_encoder(lesson, custom_encoder={ObjectId: str})
