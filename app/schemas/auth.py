from pydantic import BaseModel


class KakaoLoginRequest(BaseModel):
    code: str  # 카카오 인가코드
    redirect_uri: str  # 프론트엔드가 카카오에 보낸 redirect_uri


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
