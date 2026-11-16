from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.post import Post
from app.models.user import User
from app.repositories.post_repository import PostRepository
from app.schemas.post import PostCreate, PostUpdate


class PostService:
    def __init__(self, post_repo: PostRepository):
        self.post_repo = post_repo

    def list_posts(self, page: int, size: int) -> tuple[list[Post], int]:
        return self.post_repo.list(offset=(page - 1) * size, limit=size)

    def get_post(self, post_id: int) -> Post:
        post = self.post_repo.get_by_id(post_id)
        if not post:
            raise NotFoundError("게시글을 찾을 수 없습니다.")
        return post

    def create_post(self, data: PostCreate, user: User) -> Post:
        return self.post_repo.create(data.title, data.content, user.id)

    def update_post(self, post_id: int, data: PostUpdate, user: User) -> Post:
        post = self._get_owned_post(post_id, user)
        return self.post_repo.update(post, data.model_dump(exclude_unset=True))

    def delete_post(self, post_id: int, user: User) -> None:
        post = self._get_owned_post(post_id, user)
        self.post_repo.delete(post)

    def _get_owned_post(self, post_id: int, user: User) -> Post:
        post = self.get_post(post_id)
        if post.author_id != user.id:
            raise ForbiddenError("작성자만 수정/삭제할 수 있습니다.")
        return post
