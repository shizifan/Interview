from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T | None = None


class PaginatedData(BaseModel, Generic[T]):
    items: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


def success(data: Any = None, message: str = "success") -> dict:
    return {"code": 200, "message": message, "data": data}


def error(code: int, message: str) -> dict:
    return {"code": code, "message": message, "data": None}
