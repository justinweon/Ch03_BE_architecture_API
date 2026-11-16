from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

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
