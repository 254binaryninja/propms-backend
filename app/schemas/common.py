from pydantic import BaseModel


class PaginatedMeta(BaseModel):
    """Pagination metadata."""
    total: int
    page: int
    per_page: int
    pages: int


class Error(BaseModel):
    """Error response schema."""
    detail: str
