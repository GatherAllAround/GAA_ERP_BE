# ERD (Entity Relationship Diagram)

## 테이블 관계도

```
┌──────────────────────────┐
│          users           │
├──────────────────────────┤
│ PK  user_id    BIGSERIAL │
│     kakao_id     BIGINT  │◄─── 카카오 고유 ID
│     nickname     VARCHAR │◄─── 닉네임 (카카오에서 초기값, 수정 가능)
│     kakao_profile_image_url TEXT│◄─ 카카오 프로필 사진
│     affiliation VARCHAR  │◄─── 소속 (GAA, 외부 등)
│     role       VARCHAR   │◄─── 'root' | 'admin' | 'member'
│     created_at TIMESTAMPTZ│
│     updated_at TIMESTAMPTZ│
└─────────┬────────────────┘
          │
          │ 1:N
          ▼
┌──────────────────────────┐       ┌──────────────────────┐
│      user_sessions       │       │       sessions       │
├──────────────────────────┤       ├──────────────────────┤
│ PK  user_session_id BIGSERIAL│   │ PK  session_id BIGSERIAL│
│ FK  user_id        BIGINT│      │     name       VARCHAR│◄─ 보컬,기타,베이스...
│ FK  session_id     BIGINT│──────│     created_at TIMESTAMPTZ│
│     is_main      BOOLEAN │◄─ 메인 세션 여부           │
│     skill_level NUMERIC  │◄─ 0.00~10.00              │
│     created_at TIMESTAMPTZ│      └──────────────────────┘
└──────────────────────────┘

          │
          │
          ▼
┌──────────────────────────────┐       ┌──────────────────────┐
│        team_members          │       │        teams         │
├──────────────────────────────┤       ├──────────────────────┤
│ PK  team_member_id BIGSERIAL │       │ PK  team_id  BIGSERIAL│
│ FK  user_id          BIGINT  │       │     name     VARCHAR │
│ FK  team_id          BIGINT  │───────│     description TEXT  │
│ FK  session_id       BIGINT  │◄─ 이 팀에서 맡은 세션     │
│     joined_at    TIMESTAMPTZ │       │     created_at TIMESTAMPTZ│
└──────────────────────────────┘       └──────────────────────┘

┌───────────────────────────────┐
│    reservation_participants   │
├───────────────────────────────┤
│ PK  participant_id BIGSERIAL  │       ┌─────────────────────────┐
│ FK  reservation_id BIGINT     │──────►│      reservations       │
│ FK  user_id        BIGINT     │       ├─────────────────────────┤
│     status         VARCHAR    │       │ PK reservation_id BIGSERIAL│
│     participated_at TIMESTAMPTZ│      │ FK created_by     BIGINT│
└───────────────────────────────┘       │    title         VARCHAR│
                                        │    reservation_date DATE│
                                        │    start_time     TIME  │
                                        │    end_time       TIME  │
                                        │    location       TEXT  │
                                        │    description    TEXT  │◄─ 메모
                                        │    status         VARCHAR│
                                        │    max_participants INT │
                                        │    created_at TIMESTAMPTZ│
                                        │    updated_at TIMESTAMPTZ│
                                        └─────────────────────────┘

┌──────────────────────────┐
│         notices          │
├──────────────────────────┤
│ PK  notice_id  BIGSERIAL │
│ FK  author_id  BIGINT    │◄─── users.user_id
│     title      VARCHAR   │
│     content    TEXT       │
│     created_at TIMESTAMPTZ│
│     updated_at TIMESTAMPTZ│
└──────────────────────────┘
```

## 테이블 상세

### 1. users (회원)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| user_id | BIGSERIAL | PK | 고유 ID |
| kakao_id | BIGINT | UNIQUE, NOT NULL | 카카오 회원번호 |
| nickname | VARCHAR(100) | NOT NULL | 닉네임 (카카오에서 초기값, 수정 가능) |
| kakao_profile_image_url | TEXT | NULLABLE | 카카오 프로필 사진 URL |
| affiliation | VARCHAR(100) | NULLABLE | 소속 (GAA, 외부 등) |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'member' | 역할 (root / admin / member) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 가입일시 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 수정일시 |

### 2. sessions (세션/악기)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| session_id | BIGSERIAL | PK | 고유 ID |
| name | VARCHAR(50) | UNIQUE, NOT NULL | 세션명 (보컬, 기타, 베이스, 드럼, 키보드 등) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 생성일시 |

### 3. user_sessions (유저별 세션 매핑)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| user_session_id | BIGSERIAL | PK | 고유 ID |
| user_id | BIGINT | FK → users.user_id, NOT NULL | 회원 ID |
| session_id | BIGINT | FK → sessions.session_id, NOT NULL | 세션 ID |
| is_main | BOOLEAN | NOT NULL, DEFAULT FALSE | 메인 세션 여부 |
| skill_level | NUMERIC(4,2) | NOT NULL, DEFAULT 0.00 | 숙련도 (0.00 ~ 10.00) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 생성일시 |

> UNIQUE(user_id, session_id) — 동일 세션 중복 등록 방지

### 4. teams (팀/밴드)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| team_id | BIGSERIAL | PK | 고유 ID |
| name | VARCHAR(100) | NOT NULL | 팀 이름 |
| description | TEXT | NULLABLE | 팀 설명 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 생성일시 |

### 5. team_members (팀-회원 매핑)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| team_member_id | BIGSERIAL | PK | 고유 ID |
| team_id | BIGINT | FK → teams.team_id, NOT NULL | 팀 ID |
| user_id | BIGINT | FK → users.user_id, NOT NULL | 회원 ID |
| session_id | BIGINT | FK → sessions.session_id, NOT NULL | 이 팀에서 맡은 세션 |
| joined_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 가입일시 |

> UNIQUE(team_id, user_id) — 한 팀에 중복 가입 방지

### 6. reservations (예약)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| reservation_id | BIGSERIAL | PK | 고유 ID |
| created_by | BIGINT | FK → users.user_id, NOT NULL | 예약 생성자 |
| title | VARCHAR(255) | NOT NULL | 예약 제목 |
| reservation_date | DATE | NOT NULL | 예약 날짜 |
| start_time | TIME | NOT NULL | 시작 시간 |
| end_time | TIME | NOT NULL | 종료 시간 |
| location | TEXT | NULLABLE | 장소 |
| description | TEXT | NULLABLE | 메모 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'open' | 상태 (open / closed / cancelled) |
| max_participants | INT | NULLABLE | 최대 참가 인원 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 생성일시 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 수정일시 |

### 7. reservation_participants (예약 참가자)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| participant_id | BIGSERIAL | PK | 고유 ID |
| reservation_id | BIGINT | FK → reservations.reservation_id, NOT NULL | 예약 ID |
| user_id | BIGINT | FK → users.user_id, NOT NULL | 참가자 ID |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'confirmed' | 상태 (confirmed / cancelled) |
| participated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 참가 신청일시 |

> UNIQUE(reservation_id, user_id) — 중복 참가 방지

### 8. notices (공지사항)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| notice_id | BIGSERIAL | PK | 고유 ID |
| author_id | BIGINT | FK → users.user_id, NOT NULL | 작성자 ID |
| title | VARCHAR(255) | NOT NULL | 공지 제목 |
| content | TEXT | NOT NULL | 공지 내용 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 생성일시 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 수정일시 |

## 주요 관계 요약

| 관계 | 설명 |
|------|------|
| users ↔ sessions | N:M (user_sessions를 통한 다대다, 메인 세션 표시) |
| users ↔ teams | N:M (team_members를 통한 다대다, 팀 내 세션 지정) |
| users → reservations | 1:N (한 유저가 여러 예약 생성) |
| users ↔ reservations | N:M (reservation_participants를 통한 다대다) |
| users → notices | 1:N (한 유저가 여러 공지 작성) |

## 권한 체계

| role | 설명 | 주요 권한 |
|------|------|-----------|
| root | 최고 관리자 | 모든 권한 (운영자 임명, 시스템 설정) |
| admin | 운영자 | 멤버 관리, 공지 작성, 예약 관리 |
| member | 일반 멤버 | 예약 신청, 일정 조회, 공지 확인 |
