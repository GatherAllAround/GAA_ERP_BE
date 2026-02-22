# 게더올어라운드 총괄 프로그램 - Backend

> "가장 쉬운 모임 예약과 커뮤니티 관리"

게더올어라운드 멤버 및 운영진을 위한 통합 예약·커뮤니티 관리 시스템의 백엔드 서버입니다.

## 프로젝트 개요

- **제품명(가칭):** 게더올어라운드 총괄 프로그램
- **대상:** 게더올어라운드 멤버 및 운영진
- **핵심 가치:** 멤버들이 직접 참여하는 예약 프로세스의 시스템화 및 운영 효율화
- **개발 전략:** 비용 0원 · 웹 우선 개발 · 규모 확장 시 앱 전환 고려

## 배경 및 필요성

예약 진행 시 멤버들이 개별적으로 들어와 진행해야 하는 번거로움을 해소하기 위해, 통합 예약 시스템을 구축합니다. 멤버는 편리하게 예약하고, 운영진은 효율적으로 관리할 수 있습니다.

## 주요 기능

### 인증 (Auth)
- 카카오톡 소셜 로그인

### 예약 및 캘린더
- 월 뷰(Month View): 전체 일정 흐름 파악
- 주 뷰(Week View): 세부 시간대별 예약 현황 확인 및 신청

### 공지사항
- 주요 사항 전달 및 공지 확인

### 팀 조회
- 소속 팀 및 멤버 정보 확인

### 멤버 관리 (운영진 전용)
- 권한 부여 및 관리

## 사용자 권한

| 역할 | 권한 |
|------|------|
| 일반 멤버 (member) | 예약 신청, 일정 조회, 공지사항 확인 |
| 운영진 (admin) | 공지 작성, 세션/팀 관리, 멤버 관리 |
| 대빵 (root) | 운영진 권한 부여, 전체 시스템 관리 |

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python 3.11 / FastAPI 0.115 |
| Database | PostgreSQL (Supabase) |
| ORM | SQLAlchemy 2.0 (async) |
| Migration | Alembic |
| Auth | Kakao OAuth + JWT (python-jose) |
| Hosting | Render (Free tier) |
| 플랫폼 | Web |

## 프로젝트 구조

```
app/
├── main.py              # FastAPI 앱 진입점
├── config.py            # 환경변수 설정 (pydantic-settings)
├── database.py          # SQLAlchemy 비동기 엔진 및 세션
├── models/              # SQLAlchemy ORM 모델
├── routers/             # API 라우터 (auth, users, sessions, reservations, teams, notices)
├── schemas/             # Pydantic 요청/응답 스키마
└── services/            # 비즈니스 로직 (JWT, Kakao OAuth)
alembic/                 # DB 마이그레이션
docs/                    # ERD 등 문서
```

## 개발 환경 설정

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정
`.env.example`을 복사하여 `.env` 파일을 생성하고 값을 채웁니다.
```bash
cp .env.example .env
```

### 3. DB 마이그레이션
```bash
alembic upgrade head
```

### 4. 서버 실행
```bash
uvicorn app.main:app --reload
```
서버가 `http://localhost:8000`에서 실행됩니다.
API 문서는 `http://localhost:8000/docs`에서 확인 가능합니다.

## 배포

- **API 서버:** https://gaa-erp-be.onrender.com
- **DB:** Supabase PostgreSQL (ap-southeast-1, Singapore)
- GitHub `main` 브랜치 push 시 Render에서 자동 배포

## 로드맵

- **2026년 2월:** 기획 고도화 및 상세 설계, 화면 기획 (와이어프레임, 세미 프로토타입)
- **2026년 3월:** MVP 버전 완성 및 출시
