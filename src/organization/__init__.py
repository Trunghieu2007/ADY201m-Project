"""Package phân loại, tổ chức danh mục tự động và khám phá từ khóa xu hướng."""
from __future__ import annotations

__all__ = [
    "CANONICAL_CATEGORIES",
    "compute_category_summary",
    "extract_category_from_url",
    "get_top_keywords",
    "main",
    "organize_articles",
    "run_organization",
    "validate_summary",
]


# Nạp động các hàm và biến từ module category_organizer khi được truy xuất
def __getattr__(name: str):
    from . import category_organizer
    if hasattr(category_organizer, name):
        return getattr(category_organizer, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
