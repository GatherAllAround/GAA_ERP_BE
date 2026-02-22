# Architecture - 기술적 약속

## Communication (FE-BE 통신 규약)

### 기본 방식
- **프로토콜:** REST API (JSON)
- **Base URL:** `/api`
- **인증 헤더:** `Authorization: Bearer <JWT>`

### API 엔드포인트 구조

| Prefix | Router | 설명 |
|--------|--------|------|
| `/api/auth` | auth | 카카오 로그인, 내 정보 조회 |
| `/api/users` | users | 유저 목록, 프로필 수정, 역할 변경 |
| `/api/sessions` | sessions | 세션(악기) 관리, 유저 세션 관리 |
| `/api/reservations` | reservations | 예약 CRUD, 참여/취소 |
| `/api/teams` | teams | 팀 CRUD, 멤버 추가/삭제 |
| `/api/notices` | notices | 공지사항 CRUD |

### 공통 응답 규격
- **성공:** 각 엔드포인트별 Pydantic 스키마로 정의된 JSON 응답
- **에러:** FastAPI `HTTPException`으로 처리
  ```json
  { "detail": "에러 메시지" }
  ```
- **상태 코드:** 200 (성공), 201 (생성), 400 (잘못된 요청), 401 (인증 실패), 403 (권한 없음), 404 (미존재)

## Authentication (인증 전략)

### 인증 흐름
```
[FE] 카카오 로그인 버튼 클릭
  → 카카오 인가코드 발급
  → [BE] POST /api/auth/kakao/login { code }
    → 카카오 API로 access_token 교환
    → 카카오 API로 유저 정보 조회
    → DB에 유저 생성 또는 조회
    → JWT 발급하여 FE에 반환
  → [FE] JWT를 저장하여 이후 요청에 사용
```

### JWT 설정
- **알고리즘:** HS256
- **만료:** 7일 (604,800분)
- **Payload:** `{ "sub": "<user_id>", "exp": "<만료시간>" }`
- **검증:** `app/services/auth.py` → `get_current_user` 의존성으로 보호된 엔드포인트에 주입

### 역할 기반 접근 제어 (RBAC)
| 역할 | 코드 | 권한 범위 |
|------|------|-----------|
| 대빵 | `root` | 전체 시스템 관리, admin 권한 부여 |
| 운영진 | `admin` | 공지 작성, 세션/팀 관리, 멤버 관리 |
| 일반 멤버 | `member` | 예약 신청, 일정 조회, 공지 확인 |

권한 검사는 각 라우터 핸들러 내부에서 `current_user.role`을 확인하여 수행한다.

### 엔드포인트별 권한 정책

#### Auth (`/api/auth`)
| Method | Path | member | admin | root | 비고 |
|--------|------|:------:|:-----:|:----:|------|
| POST | `/kakao/login` | ✅ | ✅ | ✅ | 인증 불필요 (로그인) |
| GET | `/kakao/callback` | ✅ | ✅ | ✅ | 인증 불필요 (콜백) |
| GET | `/me` | ✅ | ✅ | ✅ | |

#### Users (`/api/users`)
| Method | Path | member | admin | root | 비고 |
|--------|------|:------:|:-----:|:----:|------|
| GET | `/` | ✅ | ✅ | ✅ | |
| PUT | `/me` | ✅ | ✅ | ✅ | 본인만 수정 |
| PUT | `/{user_id}/role` | ❌ | ❌ | ✅ | **root 전용** |

#### Sessions (`/api/sessions`)
| Method | Path | member | admin | root | 비고 |
|--------|------|:------:|:-----:|:----:|------|
| GET | `/` | ✅ | ✅ | ✅ | |
| POST | `/` | ❌ | ✅ | ✅ | 세션(악기) 생성 |
| GET | `/me` | ✅ | ✅ | ✅ | |
| POST | `/me` | ✅ | ✅ | ✅ | 내 악기 추가 |
| PUT | `/me/{id}` | ✅ | ✅ | ✅ | 내 악기만 수정 |
| DELETE | `/me/{id}` | ✅ | ✅ | ✅ | 내 악기만 삭제 |

#### Reservations (`/api/reservations`)
| Method | Path | member | admin | root | 비고 |
|--------|------|:------:|:-----:|:----:|------|
| GET | `/?year=&month=` | ✅ | ✅ | ✅ | |
| POST | `/` | ✅ | ✅ | ✅ | 누구나 예약 생성 |
| GET | `/{id}` | ✅ | ✅ | ✅ | |
| PUT | `/{id}` | ⚠️ | ✅ | ✅ | 본인 생성분만 수정 가능 |
| DELETE | `/{id}` | ⚠️ | ✅ | ✅ | 본인 생성분만 삭제 가능 |
| POST | `/{id}/participate` | ✅ | ✅ | ✅ | |
| DELETE | `/{id}/participate` | ✅ | ✅ | ✅ | |

#### Teams (`/api/teams`)
| Method | Path | member | admin | root | 비고 |
|--------|------|:------:|:-----:|:----:|------|
| GET | `/` | ✅ | ✅ | ✅ | |
| POST | `/` | ❌ | ✅ | ✅ | |
| GET | `/{id}` | ✅ | ✅ | ✅ | |
| PUT | `/{id}` | ❌ | ✅ | ✅ | |
| POST | `/{id}/members` | ❌ | ✅ | ✅ | |
| DELETE | `/{id}/members/{uid}` | ❌ | ✅ | ✅ | |

#### Notices (`/api/notices`)
| Method | Path | member | admin | root | 비고 |
|--------|------|:------:|:-----:|:----:|------|
| GET | `/?page=&size=` | ✅ | ✅ | ✅ | |
| POST | `/` | ❌ | ✅ | ✅ | |
| GET | `/{id}` | ✅ | ✅ | ✅ | |
| PUT | `/{id}` | ❌ | ✅ | ✅ | |
| DELETE | `/{id}` | ❌ | ✅ | ✅ | |

> ✅ 허용 | ❌ 차단 (403) | ⚠️ 조건부 (본인 생성분만)

### 프론트엔드 UI 분기 기준
- **member:** 조회 위주 + 예약 생성/참여 + 내 세션 관리
- **admin:** member 권한 + 공지/팀/세션 관리 탭 노출
- **root:** admin 권한 + 멤버 관리(역할 변경) 탭 노출

## Project Structure (폴더 구조 규칙)

```
app/
├── main.py          # FastAPI 앱 생성, 미들웨어, 라우터 등록
├── config.py        # pydantic-settings 기반 환경변수 관리
├── database.py      # SQLAlchemy 비동기 엔진, 세션 팩토리, Base 클래스
│
├── models/          # SQLAlchemy ORM 모델 (테이블 정의)
│   ├── user.py
│   ├── session.py   # Session(악기) + UserSession
│   ├── reservation.py  # Reservation + ReservationParticipant
│   ├── team.py      # Team + TeamMember
│   └── notice.py
│
├── schemas/         # Pydantic 스키마 (요청/응답 DTO)
│   ├── auth.py
│   ├── user.py
│   ├── session.py
│   ├── reservation.py
│   ├── team.py
│   └── notice.py
│
├── routers/         # API 라우터 (HTTP 엔드포인트 정의)
│   ├── auth.py
│   ├── users.py
│   ├── sessions.py
│   ├── reservations.py
│   ├── teams.py
│   └── notices.py
│
└── services/        # 비즈니스 로직 및 외부 서비스 연동
    ├── auth.py      # get_current_user 의존성
    ├── jwt.py       # JWT 생성/검증
    └── kakao.py     # 카카오 OAuth API 호출
```

### 계층 간 참조 규칙
```
routers → schemas (요청/응답 타입)
routers → models (DB 쿼리)
routers → services (인증, 비즈니스 로직)
services → models (DB 쿼리)
services → config (환경변수)
database → config (DB URL)
models → database (Base 클래스 상속)
```

### 외부 서비스 연결
| 서비스 | 용도 | 설정 |
|--------|------|------|
| Supabase PostgreSQL | 데이터 저장 | `DATABASE_URL` 환경변수 |
| Kakao OAuth API | 소셜 로그인 | `KAKAO_CLIENT_ID`, `KAKAO_REDIRECT_URI` |
| Render | 서버 호스팅 | GitHub main 브랜치 자동 배포 |
