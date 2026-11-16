# once

밝은 레트로 OS 테마의 게시판. 글 하나가 카드 한 장이고, 카드들은 세로 휠처럼 스크롤로 넘어갑니다.

FastAPI + SQLAlchemy + PostgreSQL + JWT (4계층 구조), 프론트엔드는 같은 서버가 정적 파일로 제공합니다.

## 구조

```
app/
├── main.py            # 앱 생성, 미들웨어, 예외 핸들러, 라우터와 정적 파일 등록
├── dependencies.py    # 의존성 주입 (서비스, 현재 사용자)
├── core/              # config, database, security(JWT/해싱), exceptions, storage(이미지 저장)
├── models/            # SQLAlchemy 모델 (User, Post, Like)
├── schemas/           # Pydantic 요청/응답 스키마
├── repositories/      # DB 접근 (쿼리)
├── services/          # 비즈니스 로직 (중복 체크, 작성자 검증, 좋아요, 이미지)
├── routers/           # 엔드포인트 (auth, posts)
└── static/            # 프론트엔드 (index.html, styles.css, app.js)
```

요청 흐름: `Router → Service → Repository → Model(DB)`

관계: `User 1 ─ N Post`, `User N ─ M Post` (Like 테이블, 사용자·글 조합 유니크)

## 실행 (로컬)

```bash
cp .env.example .env
docker compose up -d db
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- 화면: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- DB 호스트 포트는 5433 (다른 Postgres 와 5432 충돌 방지)
- 테이블은 서버 시작 때 자동 생성됩니다. 이전 버전으로 만든 DB 를 그대로 쓰는 경우에만 한 번 실행:
  `docker exec board-db psql -U board -d board -c "ALTER TABLE posts ADD COLUMN IF NOT EXISTS image_path VARCHAR(255);"`

## 실행 (Docker 전체, 배포용)

```bash
docker compose up -d --build
```

업로드한 사진은 `uploads` 볼륨에 보관됩니다.

## 엔드포인트

| 메서드 | 경로 | 인증 | 설명 |
|---|---|---|---|
| POST | `/auth/signup` | - | 회원가입 |
| POST | `/auth/login` | - | 로그인 (JWT 발급) |
| GET | `/auth/me` | O | 내 정보 |
| GET | `/posts` | 선택 | 목록 (`page`, `size`). 로그인 시 `liked_by_me` 포함 |
| GET | `/posts/{id}` | 선택 | 단건 조회 |
| POST | `/posts` | O | 작성 |
| PATCH | `/posts/{id}` | O (작성자) | 수정 |
| DELETE | `/posts/{id}` | O (작성자) | 삭제 (사진 파일도 함께 삭제) |
| PUT | `/posts/{id}/image` | O (작성자) | 사진 올리기/교체 (JPG·PNG·GIF·WEBP, 5MB 이하) |
| PUT | `/posts/{id}/like` | O | 좋아요 (여러 번 호출해도 한 번만 반영) |
| DELETE | `/posts/{id}/like` | O | 좋아요 취소 |

에러 응답은 `{"error": {"code", "message", "details"}}` 형식으로 통일됩니다.
