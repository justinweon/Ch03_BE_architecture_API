from fastapi import APIRouter, Depends, Query, Response, status

from app.core.exceptions import ErrorResponse
from app.dependencies import get_current_user, get_post_service
from app.models.user import User
from app.schemas.post import PostCreate, PostListResponse, PostResponse, PostUpdate
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])

AUTH_ERRORS = {401: {"model": ErrorResponse}}
OWNER_ERRORS = {**AUTH_ERRORS, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}


@router.get("", response_model=PostListResponse, summary="게시글 목록 (페이지네이션)")
def list_posts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    service: PostService = Depends(get_post_service),
):
    items, total = service.list_posts(page, size)
    return PostListResponse(items=items, total=total, page=page, size=size)


@router.get(
    "/{post_id}",
    response_model=PostResponse,
    summary="게시글 단건 조회",
    responses={404: {"model": ErrorResponse}},
)
def get_post(post_id: int, service: PostService = Depends(get_post_service)):
    return service.get_post(post_id)


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="게시글 작성 (로그인 필요)",
    responses=AUTH_ERRORS,
)
def create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    return service.create_post(data, current_user)


@router.patch(
    "/{post_id}",
    response_model=PostResponse,
    summary="게시글 수정 (작성자만)",
    responses=OWNER_ERRORS,
)
def update_post(
    post_id: int,
    data: PostUpdate,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    return service.update_post(post_id, data, current_user)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="게시글 삭제 (작성자만)",
    responses=OWNER_ERRORS,
)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    service.delete_post(post_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
