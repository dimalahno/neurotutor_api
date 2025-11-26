from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(data: LoginIn, session: AsyncSession = Depends(get_session)):
    auth = AuthService()
    try:
        user, access, refresh = await auth.login(session=session, email=data.email, password=data.password)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


class RefreshIn(BaseModel):
    refresh_token: str


@router.post("/refresh")
async def refresh(data: RefreshIn, session: AsyncSession = Depends(get_session)):
    auth = AuthService()
    try:
        access, refresh = await auth.refresh(session=session, refresh_token=data.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
