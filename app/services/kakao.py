import httpx

from app.config import settings

KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"


async def get_kakao_access_token(code: str, redirect_uri: str) -> str:
    """인가코드로 카카오 access_token을 받아온다."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            KAKAO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.kakao_client_id,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def get_kakao_user_info(access_token: str) -> dict:
    """access_token으로 카카오 유저 정보를 조회한다."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            KAKAO_USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        data = response.json()

        return {
            "kakao_id": data["id"],
            "nickname": data["kakao_account"]["profile"]["nickname"],
            "kakao_profile_image_url": data["kakao_account"]["profile"].get("profile_image_url"),
        }
