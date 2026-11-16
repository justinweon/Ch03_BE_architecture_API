from app.core import storage
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.post import Post
from app.models.user import User
from app.repositories.post_repository import PostRepository
from app.schemas.post import PostCreate, PostUpdate


class PostService:
    def __init__(self, post_repo: PostRepository):
        self.post_repo = post_repo

    def list_posts(self, page: int, size: int, user: User | None = None) -> tuple[list[Post], int]:
        posts, total = self.post_repo.list(offset=(page - 1) * size, limit=size)
        self._mark_liked(posts, user)
        return posts, total

    def get_post(self, post_id: int, user: User | None = None) -> Post:
        post = self.post_repo.get_by_id(post_id)
        if not post:
            raise NotFoundError("게시글을 찾을 수 없습니다.")
        self._mark_liked([post], user)
        return post

    def create_post(self, data: PostCreate, user: User) -> Post:
        return self.post_repo.create(data.title, data.content, user.id)

    def update_post(self, post_id: int, data: PostUpdate, user: User) -> Post:
        post = self._get_owned_post(post_id, user)
        post = self.post_repo.update(post, data.model_dump(exclude_unset=True, exclude_none=True))
        self._mark_liked([post], user)
        return post

    def delete_post(self, post_id: int, user: User) -> None:
        post = self._get_owned_post(post_id, user)
        image = post.image_path
        self.post_repo.delete(post)
        storage.delete_image(image)

    def set_image(self, post_id: int, data: bytes, user: User) -> Post:
        post = self._get_owned_post(post_id, user)
        old_image = post.image_path
        new_image = storage.save_image(data)
        post = self.post_repo.update(post, {"image_path": new_image})
        storage.delete_image(old_image)
        self._mark_liked([post], user)
        return post

    def like(self, post_id: int, user: User) -> Post:
        post = self.get_post(post_id)
        self.post_repo.add_like(post, user.id)
        post.liked_by_me = True
        return post

    def unlike(self, post_id: int, user: User) -> Post:
        post = self.get_post(post_id)
        self.post_repo.remove_like(post, user.id)
        post.liked_by_me = False
        return post

    def _mark_liked(self, posts: list[Post], user: User | None) -> None:
        liked = self.post_repo.liked_post_ids(user.id, [p.id for p in posts]) if user else set()
        for post in posts:
            post.liked_by_me = post.id in liked

    def _get_owned_post(self, post_id: int, user: User) -> Post:
        post = self.post_repo.get_by_id(post_id)
        if not post:
            raise NotFoundError("게시글을 찾을 수 없습니다.")
        if post.author_id != user.id:
            raise ForbiddenError("작성자만 수정/삭제할 수 있습니다.")
        return post
