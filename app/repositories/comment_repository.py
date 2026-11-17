from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.comment import Comment


class CommentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, comment_id: int) -> Comment | None:
        return self.db.scalar(select(Comment).options(joinedload(Comment.author)).where(Comment.id == comment_id))

    def list_by_post(self, post_id: int) -> list[Comment]:
        # author 를 join 으로 함께 로딩해 N+1 쿼리를 방지. 먼저 쓴 댓글이 위에 온다
        rows = self.db.scalars(
            select(Comment).options(joinedload(Comment.author)).where(Comment.post_id == post_id).order_by(Comment.id)
        )
        return list(rows)

    def create(self, post_id: int, author_id: int, content: str) -> Comment:
        comment = Comment(post_id=post_id, author_id=author_id, content=content)
        self.db.add(comment)
        self.db.commit()
        return self.get_by_id(comment.id)

    def delete(self, comment: Comment) -> None:
        self.db.delete(comment)
        self.db.commit()
