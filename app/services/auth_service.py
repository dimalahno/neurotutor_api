from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import create_access_token, create_refresh_token
from app.repositories.user_repositories import UserRepository, UserTokenRepository
from app.models.user_models import UserToken, User


class AuthService:
    def __init__(self, user_repo: UserRepository | None = None, token_repo: UserTokenRepository | None = None):
        self.user_repo = user_repo or UserRepository()
        self.token_repo = token_repo or UserTokenRepository()

    async def login(self, session: AsyncSession, email: str, password: str):
        from app.core.security import verify_password

        user = await self.user_repo.get_by_email(session, email)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        access = create_access_token(user=user)
        refresh = create_refresh_token(user_id=user.id)

        token = UserToken(
            user_id=user.id,
            jwt=access,
            refresh_token=refresh,
            expires_at=datetime.now(),
            created_at=datetime.now(),
        )

        session.add(token)
        await session.commit()
        await session.refresh(token)

        return user, access, refresh

    async def refresh(self, session: AsyncSession, refresh_token: str):
        from app.core.jwt import decode_token

        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        user_id = int(payload["sub"])
        user = await self.user_repo.get_by_id(session, user_id)

        access = create_access_token(user=user)
        new_refresh = create_refresh_token(user_id=user_id)

        token = UserToken(
            user_id=user_id,
            jwt=access,
            refresh_token=new_refresh,
            expires_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        session.add(token)
        await session.commit()

        return access, new_refresh
