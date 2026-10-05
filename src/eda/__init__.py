"""Package phân tích khám phá dữ liệu (Exploratory Data Analysis - EDA)."""
from __future__ import annotations

from .text_statistics import (
    average_word_length,
    character_count,
    sentence_count,
    unique_word_count,
    word_count,
)

__all__ = [
    "average_word_length",
    "character_count",
    "main",
    "sentence_count",
    "unique_word_count",
    "validate_eda_outputs",
    "word_count",
]


# Nạp động các hàm main và validate_eda_outputs từ run_eda khi được truy xuất
def __getattr__(name: str):
    if name in ("main", "validate_eda_outputs"):
        from .run_eda import main, validate_eda_outputs
        return main if name == "main" else validate_eda_outputs
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")