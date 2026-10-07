from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from src.eda import deeper_eda, temporal_analysis, text_statistics
from src.utils import (
    EXPECTED_FIELDS,
    NONEMPTY_FIELDS,
    OUTPUTS_DIR,
    RAW_DATA_PATH,
    calculate_sha256,
    describe_numeric,
    load_jsonl,
    save_json,
)
from src.validation import validate_raw

PROJECT_ROOT = RAW_DATA_PATH.parents[2]
RAW_FILE = RAW_DATA_PATH
REPORT_DIR = OUTPUTS_DIR
AUDIT_FILE = REPORT_DIR / "project_audit.json"

REQUIRED_FIELDS = NONEMPTY_FIELDS
STANDALONE_UI_PHRASES = {
    "navigation": {"trang chủ", "đăng nhập", "đăng ký", "liên hệ", "tài khoản", "menu", "home"},
    "sharing": {"chia sẻ", "theo dõi", "bình luận", "đăng lại"},
    "related_content": {"bài viết liên quan", "tin liên quan", "xem thêm", "các tin khác", "tin mới nhất", "đọc thêm"},
    "advertising": {"quảng cáo", "advertisement", "adchoices"},
}
HTML_PATTERNS = [
    r"<html\b", r"<head\b", r"<body\b", r"<script\b", r"<style\b",
    r"<iframe\b", r"<form\b", r"<nav\b", r"<footer\b", r"<header\b", r"<div\b", r"<span\b",
]
STRONG_UI_COMBINATIONS = [
    ("login_ui", re.compile(r"\b(?:đăng nhập|đăng ký)\b.{0,80}\b(?:mật khẩu|tài khoản)\b", flags=re.IGNORECASE)),
    ("share_ui", re.compile(r"\b(?:chia sẻ|theo dõi)\b.{0,80}\b(?:Facebook|Zalo|Twitter)\b", flags=re.IGNORECASE)),
    ("related_ui", re.compile(r"\b(?:bài viết liên quan|tin liên quan)\b.{0,120}\b(?:xem thêm|đọc thêm)\b", flags=re.IGNORECASE)),
]

# Tính mã băm SHA-256 của file được chỉ định
def sha256(path: Path) -> str:
    """Tính mã băm SHA-256 của file dữ liệu."""
    return calculate_sha256(path)


# Chuẩn hóa khoảng trắng đầu cuối của chuỗi
def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    return str(value).strip()


# Phát hiện rò rỉ tiêu đề hoặc mô tả trong nội dung bài viết
def detect_title_description_leakage(title: str, description: str, content: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    first_block = content.split("\n", 1)[0].strip() if content else ""
    if title and first_block.startswith(title):
        findings.append({"field": "title", "occurrences": content.count(title), "evidence": first_block[:160]})
    if description and description in content:
        findings.append({"field": "description", "occurrences": content.count(description), "evidence": first_block[:160]})
    return findings


# Phát hiện các đoạn văn bản liền kề trùng lặp nhau
def detect_adjacent_duplicate_blocks(content: str) -> dict[str, Any] | None:
    blocks = [b.strip() for b in content.splitlines() if b.strip()]
    duplicates = [
        {"block_index": i, "character_count": len(left), "preview": left[:160]}
        for i, (left, right) in enumerate(zip(blocks, blocks[1:]), start=1)
        if left == right
    ]
    return {"count": len(duplicates), "examples": duplicates[:5]} if duplicates else None


# Phát hiện thông tin ê-kíp sản xuất bị dính trong tên tác giả
def detect_mixed_author_credits(author: str) -> list[str]:
    if not author:
        return []
    markers = ["nhóm thiết kế:", "kết cấu:", "đơn vị thi công:", "ảnh:", "photo:", "biên tập:", "biên dịch:"]
    lowered = author.casefold()
    return [m for m in markers if m in lowered]


# Kiểm tra các trường bắt buộc xem có bị thiếu hoặc rỗng không
def check_required_fields(record: dict[str, Any]) -> list[str]:
    missing = []
    for field in REQUIRED_FIELDS:
        val = record.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(field)
    return missing


# Phát hiện các đoạn văn bản giao diện độc lập
def detect_standalone_ui(content: str) -> dict[str, list[str]]:
    raw_blocks = re.split(r"\n\s*\n|\r\n\s*\r\n", content)
    blocks = [normalize_text(b) for b in raw_blocks if normalize_text(b)]
    findings: dict[str, list[str]] = {}
    for block in blocks:
        if len(block) > 120:
            continue
        lowered = block.casefold()
        for category, phrases in STANDALONE_UI_PHRASES.items():
            for phrase in phrases:
                if lowered == phrase or re.fullmatch(r"^[\s\W]*" + re.escape(phrase) + r"[\s\W]*$", lowered, flags=re.IGNORECASE):
                    findings.setdefault(category, []).append(phrase)
    return findings


# Phát hiện tổ hợp từ khóa giao diện web
def detect_strong_ui_combinations(content: str) -> dict[str, str]:
    findings: dict[str, str] = {}
    for name, pattern in STRONG_UI_COMBINATIONS:
        match = pattern.search(content)
        if match:
            findings[name] = match.group(0)
    return findings


# Phát hiện thẻ HTML thô còn sót trong nội dung bài viết
def detect_html_leakage(content: str) -> list[str]:
    return [pattern for pattern in HTML_PATTERNS if re.search(pattern, content, flags=re.IGNORECASE)]


# Tính các chỉ số thống kê độ dài nội dung
def calculate_content_stats(records: list[dict[str, Any]]) -> dict[str, Any]:
    lengths = [len(normalize_text(r.get("content"))) for r in records if len(normalize_text(r.get("content"))) > 0]
    if not lengths:
        return {"count": 0, "min": 0, "max": 0, "mean": 0, "median": 0}
    return {
        "count": len(lengths),
        "min": min(lengths),
        "max": max(lengths),
        "mean": round(statistics.mean(lengths), 2),
        "median": round(statistics.median(lengths), 2),
    }


# Kiểm định chất lượng nội dung và độ toàn vẹn bóc tách văn bản
def audit_content_quality(records: list[dict[str, Any]], json_errors: list[str]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    url_counter = Counter(normalize_text(r.get("url")) for r in records if normalize_text(r.get("url")))
    title_counter = Counter(normalize_text(r.get("title")) for r in records if normalize_text(r.get("title")))
    content_counter = Counter(normalize_text(r.get("content")) for r in records if normalize_text(r.get("content")))

    for idx, record in enumerate(records, start=1):
        line_no = record.get("_line_no", idx)
        title = normalize_text(record.get("title"))
        content = normalize_text(record.get("content"))
        url = normalize_text(record.get("url"))
        record_issues: list[dict[str, Any]] = []

        leakage = detect_title_description_leakage(title, normalize_text(record.get("description")), content)
        if leakage:
            record_issues.append({"type": "title_or_description_leakage", "matches": leakage})

        adj_dups = detect_adjacent_duplicate_blocks(content)
        if adj_dups:
            record_issues.append({"type": "adjacent_duplicate_content_blocks", "details": adj_dups})

        credits_found = detect_mixed_author_credits(normalize_text(record.get("author")))
        if credits_found:
            record_issues.append({"type": "author_contains_production_credits", "markers": credits_found, "severity": "review"})

        missing_fields = check_required_fields(record)
        if missing_fields:
            record_issues.append({"type": "missing_required_field", "fields": missing_fields})

        content_length = len(content)
        if content_length == 0:
            record_issues.append({"type": "empty_content", "content_length": 0})
        elif content_length < 500:
            record_issues.append({"type": "very_short_content", "content_length": content_length})

        if url and url_counter[url] > 1:
            record_issues.append({"type": "duplicate_url", "occurrences": url_counter[url]})
        if title and title_counter[title] > 1:
            record_issues.append({"type": "duplicate_title", "occurrences": title_counter[title]})
        if content and content_counter[content] > 1:
            record_issues.append({"type": "duplicate_content", "occurrences": content_counter[content]})

        standalone_ui = detect_standalone_ui(content)
        if standalone_ui:
            record_issues.append({"type": "possible_crawler_ui_contamination", "matches": standalone_ui})

        strong_ui = detect_strong_ui_combinations(content)
        if strong_ui:
            record_issues.append({"type": "strong_ui_signal", "matches": strong_ui})

        html_matches = detect_html_leakage(content)
        if html_matches:
            record_issues.append({"type": "html_leakage", "matches": html_matches})

        replacement_count = content.count("\ufffd")
        if replacement_count:
            record_issues.append({"type": "encoding_replacement_character", "count": replacement_count})

        if record_issues:
            issues.append({"line_no": line_no, "url": url, "title": title, "content_length": content_length, "issues": record_issues})

    records_with_issues = len(issues)
    records_clean = len(records) - records_with_issues
    rate = round((records_clean / len(records)) * 100, 2) if records else 0

    return {
        "audit_metadata": {
            "dataset": str(RAW_FILE.relative_to(PROJECT_ROOT)),
            "audit_type": "raw_content_quality_and_extraction_integrity",
            "dataset_modified": False,
            "detector_version": "3.0",
        },
        "dataset_summary": {
            "records": len(records),
            "json_errors": len(json_errors),
            "records_with_issues": records_with_issues,
            "records_without_issues": records_clean,
            "issue_free_rate": rate,
        },
        "content_length_statistics": calculate_content_stats(records),
        "duplicate_summary": {
            "duplicate_urls": {u: c for u, c in url_counter.items() if c > 1},
            "duplicate_titles": {t: c for t, c in title_counter.items() if c > 1},
            "duplicate_contents_count": len([c for c in content_counter.values() if c > 1]),
        },
        "json_errors": json_errors,
        "issues": issues,
    }


# Điểm thực thi chính kiểm định toàn diện chất lượng toàn bộ dự án
def main() -> dict[str, Any]:
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Raw dataset not found: {RAW_FILE}")

    records, json_errors = validate_raw.load_jsonl(RAW_FILE)
    for idx, r in enumerate(records, start=1):
        r.setdefault("_line_no", idx)
    raw_hash = sha256(RAW_FILE)

    schema = []
    for idx, record in enumerate(records, start=1):
        missing = sorted(set(EXPECTED_FIELDS) - set(record))
        extra = sorted(set(record) - set(EXPECTED_FIELDS) - {"_line_no"})
        if missing or extra:
            schema.append({"record": idx, "missing": missing, "extra": extra})

    duplicate_urls = validate_raw.find_duplicate_urls(records)
    duplicate_titles = validate_raw.find_duplicate_values(records, "title")
    duplicate_ids = validate_raw.find_duplicate_values(records, "article_id")
    invalid_published = validate_raw.timestamp_issues(records, "published_at")
    invalid_crawled = validate_raw.timestamp_issues(records, "crawled_at")
    invalid_urls = validate_raw.invalid_urls(records)

    quality = audit_content_quality(records, json_errors)

    text_result = text_statistics.analyze_articles(records)
    temporal_result = temporal_analysis.analyze_articles(records)
    deeper_result = deeper_eda.analyze_articles(records, temporal_result)

    critical_failures = {
        "json_errors": len(json_errors),
        "schema_errors": len(schema),
        "duplicate_urls": len(duplicate_urls),
        "duplicate_titles": len(duplicate_titles),
        "duplicate_article_ids": len(duplicate_ids),
        "invalid_published_at": len(invalid_published),
        "invalid_crawled_at": len(invalid_crawled),
        "invalid_urls": len(invalid_urls),
    }

    review_issues = {
        "content_quality_records_with_issues": quality["dataset_summary"]["records_with_issues"],
        "author_review_records": sum(
            1 for item in quality["issues"]
            if any(issue.get("type") == "author_contains_production_credits" for issue in item["issues"])
        ),
    }

    result = {
        "audit": {
            "status": "PASS" if not any(critical_failures.values()) and not any(review_issues.values()) else ("PASS_WITH_REVIEW" if not any(critical_failures.values()) else "REVIEW_REQUIRED"),
            "raw_dataset_modified": False,
            "raw_sha256": raw_hash,
            "records": len(records),
        },
        "critical_failures": critical_failures,
        "review_issues": review_issues,
        "quality_audit": quality,
        "phase2_smoke": {
            "text_records": text_result["records"],
            "temporal_records": temporal_result["records"],
            "deeper_records": deeper_result["records"],
            "temporal_negative_gaps": temporal_result["publication_to_crawl_gap_minutes"]["negative_gap_count"],
        },
        "note": (
            "Audit is read-only against data/raw/articles.jsonl. Parser/validator improvements are applied "
            "to source code for future crawls; the frozen baseline raw dataset is intentionally not rewritten."
        ),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    result = main()
    print("=" * 70)
    print("ADY201m — WHOLE PROJECT AUDIT")
    print("=" * 70)
    print(f"Status: {result['audit']['status']}")
    print(f"Records: {result['audit']['records']}")
    print(f"Raw SHA-256: {result['audit']['raw_sha256']}")
