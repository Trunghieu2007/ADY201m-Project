"""Module kiểm định dữ liệu thô (Tương thích ngược, chuyển tiếp tới src.crawler.validate_raw)."""
from __future__ import annotations

from src.crawler.validate_raw import (
    ARTICLE_OUTPUT,
    EXPECTED_FIELDS,
    NONEMPTY_FIELDS,
    SUSPICIOUS_AUTHORS,
    TARGET_CATEGORIES,
    calculate_content_statistics,
    count_empty_fields,
    find_duplicate_urls,
    find_duplicate_values,
    find_suspicious_authors,
    find_suspicious_content,
    get_category_distribution,
    get_content_lengths,
    invalid_urls,
    load_jsonl,
    main,
    print_report,
    schema_issues,
    timestamp_issues,
)

__all__ = [
    "ARTICLE_OUTPUT",
    "EXPECTED_FIELDS",
    "NONEMPTY_FIELDS",
    "SUSPICIOUS_AUTHORS",
    "TARGET_CATEGORIES",
    "calculate_content_statistics",
    "count_empty_fields",
    "find_duplicate_urls",
    "find_duplicate_values",
    "find_suspicious_authors",
    "find_suspicious_content",
    "get_category_distribution",
    "get_content_lengths",
    "invalid_urls",
    "load_jsonl",
    "main",
    "print_report",
    "schema_issues",
    "timestamp_issues",
]

if __name__ == "__main__":
    main()