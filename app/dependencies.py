from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.models.user import User
from app.repositories.post_repository import PostRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.post_service import PostService

# Swagger UI 의 Authorize 버튼에 토큰만 붙여넣으면 되는 Bearer 방식
bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


def get_post_service(db: Session = Depends(get_db)) -> PostService:
    return PostService(PostRepository(db))


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    if credentials is None:
        raise UnauthorizedError("인증이 필요합니다.")
    return auth_service.get_user_from_token(credentials.credentials)


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User | None:
    """로그인 없이도 볼 수 있는 API 용. 토큰이 없거나 유효하지 않으면 비로그인으로 취급한다."""
    if credentials is None:
        return None
    try:
        return auth_service.get_user_from_token(credentials.credentials)
    except UnauthorizedError:
        return None
