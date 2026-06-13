from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


class MessageResponse(BaseModel):
    message: str
