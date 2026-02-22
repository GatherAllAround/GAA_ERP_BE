from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.user import UserListResponse, UserProfileUpdate, UserRoleUpdate
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[UserListResponse])
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """전체 멤버 목록 조회"""
    result = await db.execute(select(User).order_by(User.nickname))
    return result.scalars().all()


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내 프로필 수정 (닉네임, 소속)"""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.put("/{user_id}/role", response_model=UserListResponse)
async def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """유저 역할 변경 (root만 가능)"""
    if current_user.role != "root":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="root 권한이 필요합니다")

    if data.role not in ("root", "admin", "member"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 역할입니다")

    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다")

    user.role = data.role
    await db.commit()
    await db.refresh(user)
    return user
