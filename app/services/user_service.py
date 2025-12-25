from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_models import User, UserRole
from app.repositories.user_repositories import UserRepository, RoleDictionaryRepository
from app.core.security import hash_password, verify_password

DEFAULT_ACTIVE_STATUS_ID = 2
DEFAULT_ROLE_CODE = "USER"

class UserService:
    def __init__(
        self,
        user_repo: UserRepository | None = None,
        role_repo: RoleDictionaryRepository | None = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.role_repo = role_repo or RoleDictionaryRepository()

    async def get_all_users(self, session: AsyncSession) -> list[User]:
        return await self.user_repo.get_all(session)

    async def get_user_by_id(self, session: AsyncSession, user_id: int) -> Optional[User]:
        return await self.user_repo.get(session, user_id)


    async def create_user(
        self,
        session: AsyncSession,
        *,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        middle_name: str | None = None,
        status_id: int | None = DEFAULT_ACTIVE_STATUS_ID,
    ) -> User:
        existing = await self.user_repo.get_by_email(session, email)

        if existing:
            raise ValueError("User exists")

        if status_id is None:
            status_id = DEFAULT_ACTIVE_STATUS_ID

        user_data = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": middle_name,
            "password_hash": hash_password(password),
            "status_id": status_id,
        }
        user = await self.user_repo.create(session, user_data)
        await session.commit()
        await session.refresh(user)

        # назначаем роль по умолчанию USER
        default_role = await self.role_repo.get_by_code(session, DEFAULT_ROLE_CODE)
        if default_role:
            link = UserRole(user_id=user.id, role_id=default_role.id)
            session.add(link)

        await session.commit()
        await session.refresh(user)

        return user

    async def update_user(
            self,
            session: AsyncSession,
            user_id: int,
            **fields,
    ) -> Optional[User]:
        """Обновление пользователя по id."""

        user = await self.user_repo.get(session, user_id)
        if not user:
            return None

        allowed_fields = {
            "first_name",
            "last_name",
            "middle_name",
        }
        data = {
            key: value
            for key, value in fields.items()
            if key in allowed_fields and value is not None
        }

        if not data:
            return user

        await self.user_repo.update(session, user, data)
        await session.commit()
        await session.refresh(user)
        return user

    async def delete_user(
            self,
            session: AsyncSession,
            user_id: int,
    ) -> bool:
        """Удаление пользователя по id."""
        user = await self.user_repo.get(session, user_id)
        if not user:
            return False

        await self.user_repo.delete(session, user)
        await session.commit()
        return True


    async def change_user_role(
            self,
            session: AsyncSession,
            user_id: int,
            role_code: str,
    ) -> Optional[User]:
        """
        Изменить тип пользователя (роль) по коду роли.
        Оставляем одну основную роль: очищаем старые, назначаем новую.
        """
        user = await self.user_repo.get_by_id(session, user_id)
        if not user:
            return None

        role = await self.role_repo.get_by_code(session, role_code)
        if not role:
            raise ValueError(f"Role '{role_code}' not found")

        # чистим старые связи user_roles
        if user.role_links:
            user.role_links.clear()
            await session.flush()

        # добавляем новую связь
        new_link = UserRole(user_id=user.id, role_id=role.id)
        session.add(new_link)

        await session.commit()
        await session.refresh(user)
        return user

    async def authenticate(self, session: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await self.user_repo.get_by_email(session, email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def change_password(self, session: AsyncSession, user: User, old_password: str, new_password: str) -> bool:
        if not verify_password(old_password, user.password_hash):
            return False
        user.password_hash = hash_password(new_password)
        await session.flush()
        await session.commit()
        await session.refresh(user)
        return True
