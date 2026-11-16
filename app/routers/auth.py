from fastapi import APIRouter, Depends, status

from app.core.exceptions import ErrorResponse
from app.dependencies import get_auth_service, get_current_user
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
    responses={409: {"model": ErrorResponse}},
)
def signup(data: UserCreate, service: AuthService = Depends(get_auth_service)):
    return service.signup(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="로그인 (JWT 발급)",
    responses={401: {"model": ErrorResponse}},
)
def login(data: UserLogin, service: AuthService = Depends(get_auth_service)):
    return TokenResponse(access_token=service.login(data))


@router.get(
    "/me",
    response_model=UserResponse,
    summary="내 정보 조회",
    responses={401: {"model": ErrorResponse}},
)
def me(current_user: User = Depends(get_current_user)):
    return current_user
