from typing import List, TypeVar, Generic
from pydantic import BaseModel
from app.schemas.common import PaginatedMeta

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    data: List[T]
    meta: PaginatedMeta


def paginate(query, page: int = 1, per_page: int = 20):
    """
    Paginate a SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Tuple of (items, total_count)
    """
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return items, total


def create_pagination_meta(total: int, page: int, per_page: int) -> PaginatedMeta:
    """
    Create pagination metadata.

    Args:
        total: Total number of items
        page: Current page number
        per_page: Items per page

    Returns:
        PaginatedMeta object
    """
    pages = (total + per_page - 1) // per_page  # Ceiling division

    return PaginatedMeta(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )
