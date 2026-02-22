from datetime import datetime

from pydantic import BaseModel


class TeamCreate(BaseModel):
    name: str
    description: str | None = None


class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class AddTeamMember(BaseModel):
    user_id: int
    session_id: int


class TeamMemberResponse(BaseModel):
    user_id: int
    nickname: str
    kakao_profile_image_url: str | None
    session_name: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class TeamResponse(BaseModel):
    team_id: int
    name: str
    description: str | None
    member_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamDetailResponse(TeamResponse):
    members: list[TeamMemberResponse] = []
