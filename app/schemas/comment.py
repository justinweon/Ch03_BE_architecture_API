from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.post import AuthorResponse


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)

    @field_validator("content")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("공백만 입력할 수 없습니다.")
        return value


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    author: AuthorResponse
    created_at: datetime
