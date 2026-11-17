from fastapi import APIRouter, Depends, Response, status

from app.core.exceptions import ErrorResponse
from app.dependencies import get_comment_service, get_current_user
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.comment_service import CommentService

router = APIRouter(prefix="/posts/{post_id}/comments", tags=["comments"])

NOT_FOUND = {404: {"model": ErrorResponse}}
AUTH_ERRORS = {401: {"model": ErrorResponse}}


@router.get("", response_model=list[CommentResponse], summary="댓글 목록 (오래된 순)", responses=NOT_FOUND)
def list_comments(post_id: int, service: CommentService = Depends(get_comment_service)):
    return service.list_comments(post_id)


@router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="댓글 작성 (로그인 필요)",
    responses={**AUTH_ERRORS, **NOT_FOUND},
)
def create_comment(
    post_id: int,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
):
    return service.create_comment(post_id, data, current_user)


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="댓글 삭제 (작성자만)",
    responses={**AUTH_ERRORS, 403: {"model": ErrorResponse}, **NOT_FOUND},
)
def delete_comment(
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
):
    service.delete_comment(post_id, comment_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
