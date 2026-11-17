from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.comment import Comment
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.post_repository import PostRepository
from app.schemas.comment import CommentCreate


class CommentService:
    def __init__(self, comment_repo: CommentRepository, post_repo: PostRepository):
        self.comment_repo = comment_repo
        self.post_repo = post_repo

    def list_comments(self, post_id: int) -> list[Comment]:
        self._require_post(post_id)
        return self.comment_repo.list_by_post(post_id)

    def create_comment(self, post_id: int, data: CommentCreate, user: User) -> Comment:
        self._require_post(post_id)
        return self.comment_repo.create(post_id, user.id, data.content)

    def delete_comment(self, post_id: int, comment_id: int, user: User) -> None:
        comment = self.comment_repo.get_by_id(comment_id)
        # 주소의 글 번호와 댓글이 달린 글이 다르면 없는 댓글로 취급
        if not comment or comment.post_id != post_id:
            raise NotFoundError("댓글을 찾을 수 없습니다.")
        if comment.author_id != user.id:
            raise ForbiddenError("작성자만 삭제할 수 있습니다.")
        self.comment_repo.delete(comment)

    def _require_post(self, post_id: int) -> None:
        if not self.post_repo.get_by_id(post_id):
            raise NotFoundError("게시글을 찾을 수 없습니다.")
