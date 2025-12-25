from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db_cfg import get_async_session
from app.core.deps import get_session
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    svc = UserService()
    try:
        user = await svc.create_user(
            session,
            email=payload.email,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            middle_name=payload.middle_name,
        )
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))
    return user

@router.post("/{user_id}/role/{role_code}", response_model=UserOut)
async def change_user_role(
    user_id: int,
    role_code: str,
    session: AsyncSession = Depends(get_async_session),
):
    svc = UserService()
    user = await svc.change_user_role(session, user_id, role_code)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_session),
):
    svc = UserService()
    data = payload.model_dict(exclude_unset=True)
    user = await svc.update_user(session, user_id, **data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    svc = UserService()
    return await svc.delete_user(session, user_id)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    svc = UserService()
    user = await svc.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return user


@router.get("/", response_model=List[UserOut])
async def list_users(session: AsyncSession = Depends(get_session)):
    svc = UserService()
    return await svc.get_all_users(session)
