from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.reservation import Reservation, ReservationParticipant
from app.models.user import User
from app.schemas.reservation import (
    ReservationCreate,
    ReservationDetailResponse,
    ReservationResponse,
    ReservationUpdate,
)
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[ReservationResponse])
async def get_reservations(
    year: int = Query(..., description="조회 연도"),
    month: int = Query(..., ge=1, le=12, description="조회 월"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """예약 목록 조회 (월별, 캘린더용)"""
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    # 참가자 수 서브쿼리
    participant_count_subq = (
        select(
            ReservationParticipant.reservation_id,
            func.count().label("participant_count"),
        )
        .where(ReservationParticipant.status == "confirmed")
        .group_by(ReservationParticipant.reservation_id)
        .subquery()
    )

    result = await db.execute(
        select(Reservation, User.nickname, participant_count_subq.c.participant_count)
        .join(User, Reservation.created_by == User.user_id)
        .outerjoin(
            participant_count_subq,
            Reservation.reservation_id == participant_count_subq.c.reservation_id,
        )
        .where(
            Reservation.reservation_date >= start_date,
            Reservation.reservation_date < end_date,
        )
        .order_by(Reservation.reservation_date, Reservation.start_time)
    )
    rows = result.all()

    return [
        ReservationResponse(
            reservation_id=r.reservation_id,
            created_by=r.created_by,
            creator_nickname=nickname,
            title=r.title,
            reservation_date=r.reservation_date,
            start_time=r.start_time,
            end_time=r.end_time,
            location=r.location,
            description=r.description,
            status=r.status,
            max_participants=r.max_participants,
            participant_count=count or 0,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r, nickname, count in rows
    ]


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    data: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """예약 생성"""
    reservation = Reservation(
        created_by=current_user.user_id,
        title=data.title,
        reservation_date=data.reservation_date,
        start_time=data.start_time,
        end_time=data.end_time,
        location=data.location,
        description=data.description,
        max_participants=data.max_participants,
    )
    db.add(reservation)
    await db.commit()
    await db.refresh(reservation)

    return ReservationResponse(
        reservation_id=reservation.reservation_id,
        created_by=reservation.created_by,
        creator_nickname=current_user.nickname,
        title=reservation.title,
        reservation_date=reservation.reservation_date,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        location=reservation.location,
        description=reservation.description,
        status=reservation.status,
        max_participants=reservation.max_participants,
        participant_count=0,
        created_at=reservation.created_at,
        updated_at=reservation.updated_at,
    )


@router.get("/{reservation_id}", response_model=ReservationDetailResponse)
async def get_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """예약 상세 조회 (참가자 목록 포함)"""
    result = await db.execute(
        select(Reservation)
        .options(selectinload(Reservation.participants).selectinload(ReservationParticipant.user))
        .where(Reservation.reservation_id == reservation_id)
    )
    reservation = result.scalar_one_or_none()

    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예약을 찾을 수 없습니다")

    # 생성자 닉네임
    creator_result = await db.execute(select(User.nickname).where(User.user_id == reservation.created_by))
    creator_nickname = creator_result.scalar_one_or_none()

    confirmed_participants = [p for p in reservation.participants if p.status == "confirmed"]

    return ReservationDetailResponse(
        reservation_id=reservation.reservation_id,
        created_by=reservation.created_by,
        creator_nickname=creator_nickname,
        title=reservation.title,
        reservation_date=reservation.reservation_date,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        location=reservation.location,
        description=reservation.description,
        status=reservation.status,
        max_participants=reservation.max_participants,
        participant_count=len(confirmed_participants),
        created_at=reservation.created_at,
        updated_at=reservation.updated_at,
        participants=[
            {
                "user_id": p.user.user_id,
                "nickname": p.user.nickname,
                "kakao_profile_image_url": p.user.kakao_profile_image_url,
                "status": p.status,
                "participated_at": p.participated_at,
            }
            for p in reservation.participants
        ],
    )


@router.put("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: int,
    data: ReservationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """예약 수정 (생성자 또는 admin/root만 가능)"""
    result = await db.execute(
        select(Reservation).where(Reservation.reservation_id == reservation_id)
    )
    reservation = result.scalar_one_or_none()

    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예약을 찾을 수 없습니다")

    if reservation.created_by != current_user.user_id and current_user.role not in ("admin", "root"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="수정 권한이 없습니다")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reservation, field, value)

    await db.commit()
    await db.refresh(reservation)

    # 참가자 수 조회
    count_result = await db.execute(
        select(func.count()).where(
            ReservationParticipant.reservation_id == reservation_id,
            ReservationParticipant.status == "confirmed",
        )
    )
    participant_count = count_result.scalar()

    return ReservationResponse(
        reservation_id=reservation.reservation_id,
        created_by=reservation.created_by,
        creator_nickname=current_user.nickname,
        title=reservation.title,
        reservation_date=reservation.reservation_date,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        location=reservation.location,
        description=reservation.description,
        status=reservation.status,
        max_participants=reservation.max_participants,
        participant_count=participant_count or 0,
        created_at=reservation.created_at,
        updated_at=reservation.updated_at,
    )


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """예약 삭제 (생성자 또는 admin/root만 가능)"""
    result = await db.execute(
        select(Reservation).where(Reservation.reservation_id == reservation_id)
    )
    reservation = result.scalar_one_or_none()

    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예약을 찾을 수 없습니다")

    if reservation.created_by != current_user.user_id and current_user.role not in ("admin", "root"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="삭제 권한이 없습니다")

    await db.delete(reservation)
    await db.commit()


@router.post("/{reservation_id}/participate", status_code=status.HTTP_201_CREATED)
async def participate_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """예약 참가 신청"""
    # 예약 존재 확인
    result = await db.execute(
        select(Reservation).where(Reservation.reservation_id == reservation_id)
    )
    reservation = result.scalar_one_or_none()

    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예약을 찾을 수 없습니다")

    if reservation.status != "open":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="참가 신청이 마감된 예약입니다")

    # 이미 참가 중인지 확인
    existing = await db.execute(
        select(ReservationParticipant).where(
            ReservationParticipant.reservation_id == reservation_id,
            ReservationParticipant.user_id == current_user.user_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 참가 신청한 예약입니다")

    # 정원 확인
    if reservation.max_participants is not None:
        count_result = await db.execute(
            select(func.count()).where(
                ReservationParticipant.reservation_id == reservation_id,
                ReservationParticipant.status == "confirmed",
            )
        )
        current_count = count_result.scalar()
        if current_count >= reservation.max_participants:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="참가 정원이 초과되었습니다")

    participant = ReservationParticipant(
        reservation_id=reservation_id,
        user_id=current_user.user_id,
    )
    db.add(participant)
    await db.commit()

    return {"message": "참가 신청이 완료되었습니다"}


@router.delete("/{reservation_id}/participate", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_participation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """예약 참가 취소"""
    result = await db.execute(
        select(ReservationParticipant).where(
            ReservationParticipant.reservation_id == reservation_id,
            ReservationParticipant.user_id == current_user.user_id,
        )
    )
    participant = result.scalar_one_or_none()

    if participant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="참가 신청 내역이 없습니다")

    await db.delete(participant)
    await db.commit()
