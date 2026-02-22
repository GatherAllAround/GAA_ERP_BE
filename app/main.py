from fastapi import FastAPI

from app.routers import auth, reservations, teams, notices

app = FastAPI(
    title="게더올어라운드 총괄 프로그램 API",
    description="밴드 합주 예약 및 커뮤니티 관리 시스템",
    version="0.1.0",
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(reservations.router, prefix="/api/reservations", tags=["Reservations"])
app.include_router(teams.router, prefix="/api/teams", tags=["Teams"])
app.include_router(notices.router, prefix="/api/notices", tags=["Notices"])


@app.get("/")
async def root():
    return {"message": "GAA ERP API is running"}
