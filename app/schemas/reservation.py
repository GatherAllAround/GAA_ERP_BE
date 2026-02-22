from datetime import date, datetime, time

from pydantic import BaseModel


class ReservationCreate(BaseModel):
    title: str
    reservation_date: date
    start_time: time
    end_time: time
    location: str | None = None
    description: str | None = None
    max_participants: int | None = None


class ReservationUpdate(BaseModel):
    title: str | None = None
    reservation_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    description: str | None = None
    status: str | None = None
    max_participants: int | None = None


class ParticipantResponse(BaseModel):
    user_id: int
    nickname: str
    kakao_profile_image_url: str | None
    status: str
    participated_at: datetime

    model_config = {"from_attributes": True}


class ReservationResponse(BaseModel):
    reservation_id: int
    created_by: int
    creator_nickname: str | None = None
    title: str
    reservation_date: date
    start_time: time
    end_time: time
    location: str | None
    description: str | None
    status: str
    max_participants: int | None
    participant_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReservationDetailResponse(ReservationResponse):
    participants: list[ParticipantResponse] = []
