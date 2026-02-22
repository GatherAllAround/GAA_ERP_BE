from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.session import Session, UserSession
from app.models.user import User
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    UserSessionCreate,
    UserSessionResponse,
    UserSessionUpdate,
)
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[SessionResponse])
async def get_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """세션(악기) 목록 조회"""
    result = await db.execute(select(Session).order_by(Session.name))
    return result.scalars().all()


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """세션(악기) 추가 (admin/root)"""
    if current_user.role not in ("admin", "root"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다")

    existing = await db.execute(select(Session).where(Session.name == data.name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 존재하는 세션입니다")

    session = Session(name=data.name)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


# --- 내 세션 관리 ---


@router.get("/me", response_model=list[UserSessionResponse])
async def get_my_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내 세션(악기) 목록 조회"""
    result = await db.execute(
        select(UserSession, Session.name)
        .join(Session, UserSession.session_id == Session.session_id)
        .where(UserSession.user_id == current_user.user_id)
        .order_by(UserSession.is_main.desc(), Session.name)
    )
    rows = result.all()

    return [
        UserSessionResponse(
            user_session_id=us.user_session_id,
            session_id=us.session_id,
            session_name=name,
            is_main=us.is_main,
            skill_level=us.skill_level,
            created_at=us.created_at,
        )
        for us, name in rows
    ]


@router.post("/me", response_model=UserSessionResponse, status_code=status.HTTP_201_CREATED)
async def add_my_session(
    data: UserSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내 세션(악기) 등록"""
    # 세션 존재 확인
    session_result = await db.execute(select(Session).where(Session.session_id == data.session_id))
    session = session_result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다")

    # 중복 확인
    existing = await db.execute(
        select(UserSession).where(
            UserSession.user_id == current_user.user_id,
            UserSession.session_id == data.session_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 등록된 세션입니다")

    # 메인 세션 설정 시 기존 메인 해제
    if data.is_main:
        existing_main = await db.execute(
            select(UserSession).where(
                UserSession.user_id == current_user.user_id,
                UserSession.is_main == True,
            )
        )
        for us in existing_main.scalars().all():
            us.is_main = False

    user_session = UserSession(
        user_id=current_user.user_id,
        session_id=data.session_id,
        is_main=data.is_main,
        skill_level=data.skill_level,
    )
    db.add(user_session)
    await db.commit()
    await db.refresh(user_session)

    return UserSessionResponse(
        user_session_id=user_session.user_session_id,
        session_id=user_session.session_id,
        session_name=session.name,
        is_main=user_session.is_main,
        skill_level=user_session.skill_level,
        created_at=user_session.created_at,
    )


@router.put("/me/{user_session_id}", response_model=UserSessionResponse)
async def update_my_session(
    user_session_id: int,
    data: UserSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내 세션(악기) 수정"""
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_session_id == user_session_id,
            UserSession.user_id == current_user.user_id,
        )
    )
    user_session = result.scalar_one_or_none()

    if user_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다")

    # 메인 세션 변경 시 기존 메인 해제
    if data.is_main is True:
        existing_main = await db.execute(
            select(UserSession).where(
                UserSession.user_id == current_user.user_id,
                UserSession.is_main == True,
                UserSession.user_session_id != user_session_id,
            )
        )
        for us in existing_main.scalars().all():
            us.is_main = False

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user_session, field, value)

    await db.commit()
    await db.refresh(user_session)

    session_result = await db.execute(select(Session.name).where(Session.session_id == user_session.session_id))
    session_name = session_result.scalar_one()

    return UserSessionResponse(
        user_session_id=user_session.user_session_id,
        session_id=user_session.session_id,
        session_name=session_name,
        is_main=user_session.is_main,
        skill_level=user_session.skill_level,
        created_at=user_session.created_at,
    )


@router.delete("/me/{user_session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_session(
    user_session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내 세션(악기) 삭제"""
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_session_id == user_session_id,
            UserSession.user_id == current_user.user_id,
        )
    )
    user_session = result.scalar_one_or_none()

    if user_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다")

    await db.delete(user_session)
    await db.commit()
