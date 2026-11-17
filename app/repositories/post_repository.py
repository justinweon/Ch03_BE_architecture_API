from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, joinedload

from app.models.like import Like
from app.models.post import Post


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, post_id: int) -> Post | None:
        # author 를 join 으로 함께 로딩해 N+1 쿼리를 방지
        return self.db.scalar(select(Post).options(joinedload(Post.author)).where(Post.id == post_id))

    def list(self, offset: int, limit: int) -> tuple[list[Post], int]:
        total = self.db.scalar(select(func.count()).select_from(Post)) or 0
        items = self.db.scalars(
            select(Post)
            .options(joinedload(Post.author))
            .order_by(Post.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return list(items), total

    def create(self, title: str, content: str, author_id: int) -> Post:
        post = Post(title=title, content=content, author_id=author_id)
        self.db.add(post)
        self.db.commit()
        return self.get_by_id(post.id)

    def update(self, post: Post, data: dict) -> Post:
        for key, value in data.items():
            setattr(post, key, value)
        self.db.commit()
        self.db.refresh(post)
        return post

    def delete(self, post: Post) -> None:
        self.db.delete(post)
        self.db.commit()

    def liked_post_ids(self, user_id: int, post_ids: list[int]) -> set[int]:
        """목록의 글들 중 사용자가 좋아요한 글 id 를 한 번의 쿼리로 조회."""
        if not post_ids:
            return set()
        rows = self.db.scalars(
            select(Like.post_id).where(Like.user_id == user_id, Like.post_id.in_(post_ids))
        )
        return set(rows)

    def add_like(self, post: Post, user_id: int) -> None:
        # 이미 눌렀으면 아무 일도 하지 않음 (PUT 멱등성). 동시 요청도 유니크 제약으로 안전
        self.db.execute(
            insert(Like).values(user_id=user_id, post_id=post.id).on_conflict_do_nothing(constraint="uq_likes_user_post")
        )
        self.db.commit()
        self.db.refresh(post)

    def remove_like(self, post: Post, user_id: int) -> None:
        self.db.execute(delete(Like).where(Like.user_id == user_id, Like.post_id == post.id))
        self.db.commit()
        self.db.refresh(post)
