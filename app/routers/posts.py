from fastapi import APIRouter, Depends, Query, Response, UploadFile, status

from app.core.config import settings
from app.core.exceptions import ErrorResponse
from app.dependencies import get_current_user, get_current_user_optional, get_post_service
from app.models.user import User
from app.schemas.post import PostCreate, PostListResponse, PostResponse, PostUpdate
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])

NOT_FOUND = {404: {"model": ErrorResponse}}
AUTH_ERRORS = {401: {"model": ErrorResponse}}
OWNER_ERRORS = {**AUTH_ERRORS, 403: {"model": ErrorResponse}, **NOT_FOUND}


@router.get("", response_model=PostListResponse, summary="게시글 목록 (페이지네이션)")
def list_posts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User | None = Depends(get_current_user_optional),
    service: PostService = Depends(get_post_service),
):
    items, total = service.list_posts(page, size, current_user)
    return PostListResponse(items=items, total=total, page=page, size=size)


@router.get("/{post_id}", response_model=PostResponse, summary="게시글 단건 조회", responses=NOT_FOUND)
def get_post(
    post_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    service: PostService = Depends(get_post_service),
):
    return service.get_post(post_id, current_user)


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


@router.patch("/{post_id}", response_model=PostResponse, summary="게시글 수정 (작성자만)", responses=OWNER_ERRORS)
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


@router.put(
    "/{post_id}/image",
    response_model=PostResponse,
    summary="게시글 사진 올리기/교체 (작성자만, JPG·PNG·GIF·WEBP, 5MB 이하)",
    responses={**OWNER_ERRORS, 413: {"model": ErrorResponse}, 415: {"model": ErrorResponse}},
)
def upload_post_image(
    post_id: int,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    # 제한보다 1바이트만 더 읽어, 큰 파일을 통째로 메모리에 올리지 않고 초과 여부를 판단
    data = file.file.read(settings.MAX_UPLOAD_BYTES + 1)
    return service.set_image(post_id, data, current_user)


@router.put(
    "/{post_id}/like",
    response_model=PostResponse,
    summary="좋아요 (로그인 필요, 여러 번 눌러도 한 번만 반영)",
    responses={**AUTH_ERRORS, **NOT_FOUND},
)
def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    return service.like(post_id, current_user)


@router.delete(
    "/{post_id}/like",
    response_model=PostResponse,
    summary="좋아요 취소 (로그인 필요)",
    responses={**AUTH_ERRORS, **NOT_FOUND},
)
def unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    return service.unlike(post_id, current_user)
