from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.session import Session
from app.models.team import Team, TeamMember
from app.models.user import User
from app.schemas.team import (
    AddTeamMember,
    TeamCreate,
    TeamDetailResponse,
    TeamResponse,
    TeamUpdate,
)
from app.services.auth import get_current_user

router = APIRouter()


def require_admin(user: User):
    """admin 또는 root 권한 확인"""
    if user.role not in ("admin", "root"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다")


@router.get("/", response_model=list[TeamResponse])
async def get_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """팀 목록 조회"""
    member_count_subq = (
        select(TeamMember.team_id, func.count().label("member_count"))
        .group_by(TeamMember.team_id)
        .subquery()
    )

    result = await db.execute(
        select(Team, member_count_subq.c.member_count)
        .outerjoin(member_count_subq, Team.team_id == member_count_subq.c.team_id)
        .order_by(Team.created_at)
    )
    rows = result.all()

    return [
        TeamResponse(
            team_id=team.team_id,
            name=team.name,
            description=team.description,
            member_count=count or 0,
            created_at=team.created_at,
        )
        for team, count in rows
    ]


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """팀 생성 (root/admin)"""
    require_admin(current_user)

    team = Team(name=data.name, description=data.description)
    db.add(team)
    await db.commit()
    await db.refresh(team)

    return TeamResponse(
        team_id=team.team_id,
        name=team.name,
        description=team.description,
        member_count=0,
        created_at=team.created_at,
    )


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """팀 상세 조회 (멤버 목록 포함)"""
    result = await db.execute(
        select(Team)
        .options(
            selectinload(Team.members).selectinload(TeamMember.user),
            selectinload(Team.members).selectinload(TeamMember.session),
        )
        .where(Team.team_id == team_id)
    )
    team = result.scalar_one_or_none()

    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="팀을 찾을 수 없습니다")

    return TeamDetailResponse(
        team_id=team.team_id,
        name=team.name,
        description=team.description,
        member_count=len(team.members),
        created_at=team.created_at,
        members=[
            {
                "user_id": m.user.user_id,
                "nickname": m.user.nickname,
                "kakao_profile_image_url": m.user.kakao_profile_image_url,
                "session_name": m.session.name,
                "joined_at": m.joined_at,
            }
            for m in team.members
        ],
    )


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """팀 수정 (root/admin)"""
    require_admin(current_user)

    result = await db.execute(select(Team).where(Team.team_id == team_id))
    team = result.scalar_one_or_none()

    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="팀을 찾을 수 없습니다")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    await db.commit()
    await db.refresh(team)

    count_result = await db.execute(
        select(func.count()).where(TeamMember.team_id == team_id)
    )

    return TeamResponse(
        team_id=team.team_id,
        name=team.name,
        description=team.description,
        member_count=count_result.scalar() or 0,
        created_at=team.created_at,
    )


@router.post("/{team_id}/members", status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: int,
    data: AddTeamMember,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """팀 멤버 추가 (root/admin)"""
    require_admin(current_user)

    # 팀 존재 확인
    team = await db.execute(select(Team).where(Team.team_id == team_id))
    if team.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="팀을 찾을 수 없습니다")

    # 유저 존재 확인
    user = await db.execute(select(User).where(User.user_id == data.user_id))
    if user.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다")

    # 세션 존재 확인
    session = await db.execute(select(Session).where(Session.session_id == data.session_id))
    if session.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다")

    # 중복 확인
    existing = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == data.user_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 팀에 소속된 멤버입니다")

    member = TeamMember(team_id=team_id, user_id=data.user_id, session_id=data.session_id)
    db.add(member)
    await db.commit()

    return {"message": "멤버가 추가되었습니다"}


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """팀 멤버 제거 (root/admin)"""
    require_admin(current_user)

    result = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
    )
    member = result.scalar_one_or_none()

    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 팀 멤버를 찾을 수 없습니다")

    await db.delete(member)
    await db.commit()
