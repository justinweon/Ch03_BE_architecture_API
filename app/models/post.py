from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.core.database import Base
from app.models.comment import Comment
from app.models.like import Like


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    author: Mapped["User"] = relationship(back_populates="posts")
    likes: Mapped[list[Like]] = relationship(cascade="all, delete-orphan", passive_deletes=True)
    comments: Mapped[list[Comment]] = relationship(cascade="all, delete-orphan", passive_deletes=True)

    # 글을 조회하는 같은 쿼리 안에서 좋아요 수를 서브쿼리로 계산 (글마다 추가 쿼리 없음)
    like_count: Mapped[int] = column_property(
        select(func.count(Like.id)).where(Like.post_id == id).correlate_except(Like).scalar_subquery()
    )

    comment_count: Mapped[int] = column_property(
        select(func.count(Comment.id)).where(Comment.post_id == id).correlate_except(Comment).scalar_subquery()
    )

    # 요청한 사용자가 좋아요를 눌렀는지. 서비스 계층에서 채워 주는 값 (DB 컬럼 아님)
    liked_by_me = False

    @property
    def image_url(self) -> str | None:
        return f"/uploads/{self.image_path}" if self.image_path else None
