from pydantic import BaseModel


class KakaoLoginRequest(BaseModel):
    code: str  # 카카오 인가코드


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    user_id: int
    kakao_id: int
    nickname: str
    kakao_profile_image_url: str | None
    affiliation: str | None
    role: str

    model_config = {"from_attributes": True}
