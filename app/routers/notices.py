from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notice import Notice
from app.models.user import User
from app.schemas.notice import NoticeCreate, NoticeResponse, NoticeUpdate
from app.services.auth import get_current_user

router = APIRouter()


def require_admin(user: User):
    if user.role not in ("admin", "root"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다")


@router.get("/", response_model=list[NoticeResponse])
async def get_notices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """공지사항 목록 조회 (페이지네이션)"""
    offset = (page - 1) * size

    result = await db.execute(
        select(Notice, User.nickname)
        .join(User, Notice.author_id == User.user_id)
        .order_by(Notice.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    rows = result.all()

    return [
        NoticeResponse(
            notice_id=notice.notice_id,
            author_id=notice.author_id,
            author_nickname=nickname,
            title=notice.title,
            content=notice.content,
            created_at=notice.created_at,
            updated_at=notice.updated_at,
        )
        for notice, nickname in rows
    ]


@router.post("/", response_model=NoticeResponse, status_code=status.HTTP_201_CREATED)
async def create_notice(
    data: NoticeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """공지사항 작성 (root/admin)"""
    require_admin(current_user)

    notice = Notice(
        author_id=current_user.user_id,
        title=data.title,
        content=data.content,
    )
    db.add(notice)
    await db.commit()
    await db.refresh(notice)

    return NoticeResponse(
        notice_id=notice.notice_id,
        author_id=notice.author_id,
        author_nickname=current_user.nickname,
        title=notice.title,
        content=notice.content,
        created_at=notice.created_at,
        updated_at=notice.updated_at,
    )


@router.get("/{notice_id}", response_model=NoticeResponse)
async def get_notice(
    notice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """공지사항 상세 조회"""
    result = await db.execute(
        select(Notice, User.nickname)
        .join(User, Notice.author_id == User.user_id)
        .where(Notice.notice_id == notice_id)
    )
    row = result.one_or_none()

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="공지사항을 찾을 수 없습니다")

    notice, nickname = row

    return NoticeResponse(
        notice_id=notice.notice_id,
        author_id=notice.author_id,
        author_nickname=nickname,
        title=notice.title,
        content=notice.content,
        created_at=notice.created_at,
        updated_at=notice.updated_at,
    )


@router.put("/{notice_id}", response_model=NoticeResponse)
async def update_notice(
    notice_id: int,
    data: NoticeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """공지사항 수정 (root/admin)"""
    require_admin(current_user)

    result = await db.execute(select(Notice).where(Notice.notice_id == notice_id))
    notice = result.scalar_one_or_none()

    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="공지사항을 찾을 수 없습니다")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notice, field, value)

    await db.commit()
    await db.refresh(notice)

    return NoticeResponse(
        notice_id=notice.notice_id,
        author_id=notice.author_id,
        author_nickname=current_user.nickname,
        title=notice.title,
        content=notice.content,
        created_at=notice.created_at,
        updated_at=notice.updated_at,
    )


@router.delete("/{notice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notice(
    notice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """공지사항 삭제 (root/admin)"""
    require_admin(current_user)

    result = await db.execute(select(Notice).where(Notice.notice_id == notice_id))
    notice = result.scalar_one_or_none()

    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="공지사항을 찾을 수 없습니다")

    await db.delete(notice)
    await db.commit()
