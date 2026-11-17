from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("title", "content")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("공백만 입력할 수 없습니다.")
        return value


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=2000)

    @field_validator("title", "content")
    @classmethod
    def not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("공백만 입력할 수 없습니다.")
        return value


class AuthorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    image_url: str | None = None
    like_count: int = 0
    comment_count: int = 0
    liked_by_me: bool = False
    author: AuthorResponse
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    items: list[PostResponse]
    total: int
    page: int
    size: int
