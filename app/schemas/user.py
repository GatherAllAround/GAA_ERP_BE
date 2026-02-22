from pydantic import BaseModel


class UserProfileUpdate(BaseModel):
    nickname: str | None = None
    affiliation: str | None = None


class UserRoleUpdate(BaseModel):
    role: str  # root, admin, member


class UserListResponse(BaseModel):
    user_id: int
    kakao_id: int
    nickname: str
    kakao_profile_image_url: str | None
    affiliation: str | None
    role: str

    model_config = {"from_attributes": True}
