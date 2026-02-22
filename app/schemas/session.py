from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SessionResponse(BaseModel):
    session_id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    name: str


class UserSessionCreate(BaseModel):
    session_id: int
    is_main: bool = False
    skill_level: Decimal = Field(default=Decimal("0.00"), ge=0, le=10)


class UserSessionUpdate(BaseModel):
    is_main: bool | None = None
    skill_level: Decimal | None = Field(default=None, ge=0, le=10)


class UserSessionResponse(BaseModel):
    user_session_id: int
    session_id: int
    session_name: str
    is_main: bool
    skill_level: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}
