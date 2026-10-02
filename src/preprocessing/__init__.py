"""Module tiền xử lý và làm sạch dữ liệu bài viết (Phase T - Transform)."""
from __future__ import annotations

__all__ = [
    "DESCRIPTIVE_FEATURES",
    "FEATURE_MATRIX_OUTPUT",
    "PROCESSED_OUTPUT",
    "RAW",
    "lexical_features",
    "normalize_author",
    "normalize_text",
    "normalize_unicode",
    "preprocess_record",
    "remove_leading_duplicate_blocks",
    "run",
    "main",
    "sentence_count",
    "tokenize",
    "validate",
]


def __getattr__(name: str):
    from . import preprocess
    if hasattr(preprocess, name):
        return getattr(preprocess, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
