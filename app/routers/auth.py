from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import KakaoLoginRequest, TokenResponse, UserResponse
from app.services.auth import get_current_user
from app.services.jwt import create_access_token
from app.services.kakao import get_kakao_access_token, get_kakao_user_info

router = APIRouter()


@router.get("/kakao/callback")
async def kakao_callback(code: str, db: AsyncSession = Depends(get_db)):
    """
    카카오 로그인 콜백 (브라우저 redirect용)
    카카오에서 인가코드를 받아 자동으로 로그인 처리 후 JWT 반환
    """
    try:
        kakao_token = await get_kakao_access_token(code, settings.kakao_redirect_uri)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="카카오 인가코드가 유효하지 않습니다")

    try:
        kakao_user = await get_kakao_user_info(kakao_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="카카오 유저 정보 조회에 실패했습니다")

    result = await db.execute(select(User).where(User.kakao_id == kakao_user["kakao_id"]))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            kakao_id=kakao_user["kakao_id"],
            nickname=kakao_user["nickname"],
            kakao_profile_image_url=kakao_user.get("kakao_profile_image_url"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token(user.user_id)
    return TokenResponse(access_token=access_token)


@router.post("/kakao/login", response_model=TokenResponse)
async def kakao_login(request: KakaoLoginRequest, db: AsyncSession = Depends(get_db)):
    """
    카카오 로그인
    1. 인가코드로 카카오 access_token 발급
    2. access_token으로 유저 정보 조회
    3. DB에 유저 생성 또는 조회
    4. JWT 발급
    """
    try:
        kakao_token = await get_kakao_access_token(request.code, request.redirect_uri)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="카카오 인가코드가 유효하지 않습니다")

    try:
        kakao_user = await get_kakao_user_info(kakao_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="카카오 유저 정보 조회에 실패했습니다")

    # DB에서 유저 조회
    result = await db.execute(select(User).where(User.kakao_id == kakao_user["kakao_id"]))
    user = result.scalar_one_or_none()

    if user is None:
        # 신규 유저 생성
        user = User(
            kakao_id=kakao_user["kakao_id"],
            nickname=kakao_user["nickname"],
            kakao_profile_image_url=kakao_user.get("kakao_profile_image_url"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # JWT 발급
    access_token = create_access_token(user.user_id)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """현재 로그인한 유저 정보 조회"""
    return current_user
