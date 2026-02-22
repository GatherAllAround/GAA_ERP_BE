from datetime import datetime

from pydantic import BaseModel


class NoticeCreate(BaseModel):
    title: str
    content: str


class NoticeUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class NoticeResponse(BaseModel):
    notice_id: int
    author_id: int
    author_nickname: str | None = None
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
