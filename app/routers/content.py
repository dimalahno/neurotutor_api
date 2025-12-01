from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status

from app.config.mongo_cfg import mongo_db

router = APIRouter(prefix="/content", tags=["content"],)


@router.get("/courses")
async def list_courses() -> List[Dict[str, Any]]:
    cursor = mongo_db["courses"].find({})
    courses = await cursor.to_list(length=1000)
    return courses


@router.get("/courses/{course_id}")
async def get_course(course_id: str) -> Dict[str, Any]:
    course = await mongo_db["courses"].find_one({"_id": course_id})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    return course


@router.get("/lessons")
async def list_lessons() -> List[Dict[str, Any]]:
    cursor = mongo_db["lessons"].find({})
    lessons = await cursor.to_list(length=1000)
    return lessons


@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: str) -> Dict[str, Any]:
    lesson = await mongo_db["lessons"].find_one({"_id": lesson_id})
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )
    return lesson
