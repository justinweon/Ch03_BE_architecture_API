import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import app.models  # noqa: F401  (모델을 Base.metadata 에 등록)
from app.core import storage
from app.core.database import Base, engine
from app.core.exceptions import register_exception_handlers
from app.routers import auth, posts

logger = logging.getLogger("board")
logging.basicConfig(level=logging.INFO)

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 테이블 자동 생성. 스키마가 커지면 Alembic 마이그레이션으로 교체
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Board API",
    description="RESTful 게시판 API (FastAPI + SQLAlchemy + PostgreSQL + JWT)",
    version="0.3.0",
    lifespan=lifespan,
)

# 프론트엔드를 같은 서버에서 제공하므로 운영에서는 allow_origins 를 실제 도메인으로 좁힐 것
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s (%.1fms)", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


register_exception_handlers(app)
app.include_router(auth.router)
app.include_router(posts.router)


@app.get("/health", tags=["health"], summary="헬스 체크")
def health():
    return {"status": "ok"}


# 정적 파일은 API 라우터 뒤에 등록해야 /auth, /posts, /docs 가 먼저 매칭된다
app.mount("/uploads", StaticFiles(directory=storage.upload_dir()), name="uploads")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
