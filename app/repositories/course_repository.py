from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course_model import Course
from app.schemas.course_schema import CourseCreate, CourseUpdate


class CourseRepository:
    @staticmethod
    async def upsert_by_mongo_id(
        session: AsyncSession,
        mongo_course_id: str,
        title: str,
        description: str,
        level: str | None = None,
    ) -> Course:
        result = await session.execute(
            select(Course).where(Course.mongo_course_id == mongo_course_id)
        )
        course: Optional[Course] = result.scalar_one_or_none()

        if course is None:
            course = Course(
                mongo_course_id=mongo_course_id,
                title=title,
                description=description,
                level=level,
            )
            session.add(course)
        else:
            course.title = title
            course.description = description
            course.level = level

        await session.flush()
        await session.refresh(course)
        return course

    @staticmethod
    async def create(session: AsyncSession, data: CourseCreate) -> Course:
        course = Course(**data.model_fields_set)
        session.add(course)
        await session.flush()
        await session.refresh(course)
        return course

    @staticmethod
    async def get_by_id(session: AsyncSession, course_id: int) -> Optional[Course]:
        result = await session.execute(
            select(Course).where(Course.id == course_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_mongo_id(
        session: AsyncSession, mongo_course_id: str
    ) -> Optional[Course]:
        result = await session.execute(
            select(Course).where(Course.mongo_course_id == mongo_course_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(session: AsyncSession) -> List[Course]:
        result = await session.execute(select(Course))
        return result.scalars().all()

    @staticmethod
    async def update(
        session: AsyncSession, course: Course, data: CourseUpdate
    ) -> Course:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(course, field, value)
        await session.flush()
        await session.refresh(course)
        return course
