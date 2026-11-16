# Ch03_BE_architecture_API

RESTful 게시판 API — FastAPI + SQLAlchemy + PostgreSQL + JWT (4계층 구조)

## 구조

```
app/
├── main.py            # 앱 생성, 미들웨어, 예외 핸들러, 라우터 등록
├── dependencies.py    # 의존성 주입 (서비스, 현재 사용자)
├── core/              # config, database, security(JWT/해싱), exceptions
├── models/            # SQLAlchemy 모델 (User, Post)
├── schemas/           # Pydantic 요청/응답 스키마
├── repositories/      # DB 접근 (쿼리)
├── services/          # 비즈니스 로직 (중복 체크, 작성자 검증)
└── routers/           # 엔드포인트 (auth, posts)
```

요청 흐름: `Router → Service → Repository → Model(DB)`

## 실행 (로컬)

```bash
cp .env.example .env
docker compose up -d db
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- DB 호스트 포트는 5433 (다른 Postgres 와 5432 충돌 방지)
- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

## 실행 (Docker 전체, 배포용)

```bash
docker compose up -d --build
```

## 엔드포인트

| 메서드 | 경로 | 인증 | 설명 |
|---|---|---|---|
| POST | `/auth/signup` | - | 회원가입 |
| POST | `/auth/login` | - | 로그인 (JWT 발급) |
| GET | `/auth/me` | O | 내 정보 |
| GET | `/posts` | - | 목록 (`page`, `size`) |
| GET | `/posts/{id}` | - | 단건 조회 |
| POST | `/posts` | O | 작성 |
| PATCH | `/posts/{id}` | O (작성자) | 수정 |
| DELETE | `/posts/{id}` | O (작성자) | 삭제 |

에러 응답은 `{"error": {"code", "message", "details"}}` 형식으로 통일됩니다.
