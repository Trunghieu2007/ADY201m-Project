from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FILE = PROJECT_ROOT / "data" / "raw" / "articles.jsonl"
REPORT_DIR = PROJECT_ROOT / "outputs"
MANIFEST_FILE = REPORT_DIR / "dataset_manifest.json"

EXPECTED_SCHEMA = [
    "url", "title", "description", "content", "author", "publisher",
    "published_at", "category", "subcategory", "article_id", "crawled_at", "source",
]


def calculate_sha256(path: Path) -> str:
    # Tính mã băm SHA-256 của toàn bộ tệp dữ liệu thô
    sha256 = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_records(path: Path) -> list[dict[str, Any]]:
    # Đọc danh sách bản ghi JSONL mà không làm thay đổi tệp gốc
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at line {line_no}: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Line {line_no} is not a JSON object")
            records.append(record)
    return records


def inspect_schema(records: list[dict[str, Any]]) -> dict[str, Any]:
    # Xác thực cấu trúc schema chuẩn trên từng bản ghi
    expected_fields = set(EXPECTED_SCHEMA)
    actual_union: set[str] = set()
    records_with_missing_fields: dict[str, list[str]] = {}
    records_with_unexpected_fields: dict[str, list[str]] = {}

    for index, record in enumerate(records, start=1):
        actual = set(record.keys())
        actual_union.update(actual)
        missing = sorted(expected_fields - actual)
        unexpected = sorted(actual - expected_fields)
        record_key = str(record.get("article_id") or f"record_{index}")
        if missing:
            records_with_missing_fields[record_key] = missing
        if unexpected:
            records_with_unexpected_fields[record_key] = unexpected

    return {
        "expected_fields": EXPECTED_SCHEMA,
        "actual_fields": sorted(actual_union),
        "missing_fields": sorted(expected_fields - actual_union),
        "unexpected_fields": sorted(actual_union - expected_fields),
        "records_with_missing_fields": records_with_missing_fields,
        "records_with_unexpected_fields": records_with_unexpected_fields,
        "schema_matches_expected": not records_with_missing_fields and not records_with_unexpected_fields,
    }


def category_distribution(records: list[dict[str, Any]]) -> dict[str, int]:
    # Đếm số lượng bài báo theo chuyên mục
    return dict(sorted(Counter(str(r.get("category", "")).strip() for r in records).items()))


def subcategory_distribution(records: list[dict[str, Any]]) -> dict[str, int]:
    # Đếm số lượng bài báo theo tiểu mục
    return dict(sorted(Counter(str(r.get("subcategory", "")).strip() for r in records).items()))


def duplicate_count(records: list[dict[str, Any]], field: str) -> int:
    # Đếm số giá trị bị trùng lặp của một trường dữ liệu
    values = [str(r.get(field, "")).strip() for r in records if str(r.get(field, "")).strip()]
    return len(values) - len(set(values))


def field_completeness(records: list[dict[str, Any]]) -> dict[str, int]:
    # Đếm số bản ghi có dữ liệu hợp lệ cho từng trường
    res: dict[str, int] = {}
    for f in EXPECTED_SCHEMA:
        res[f] = sum(1 for r in records if r.get(f) is not None and (not isinstance(r.get(f), str) or bool(str(r.get(f)).strip())))
    return res


def build_manifest(records: list[dict[str, Any]]) -> dict[str, Any]:
    # Tạo đối tượng manifest đầy đủ cho tập dữ liệu thô
    schema = inspect_schema(records)
    completeness = field_completeness(records)
    return {
        "manifest_version": "1.0",
        "dataset": {
            "name": "ADY201m Raw Dataset v1",
            "path": str(RAW_FILE.relative_to(PROJECT_ROOT)),
            "format": "JSONL",
            "source": "VnExpress",
            "records": len(records),
            "file_size_bytes": RAW_FILE.stat().st_size,
            "sha256": calculate_sha256(RAW_FILE),
        },
        "created_at": datetime.now().astimezone().isoformat(),
        "schema": schema,
        "field_completeness": completeness,
        "category_distribution": category_distribution(records),
        "subcategory_distribution": subcategory_distribution(records),
        "duplicates": {
            "url": duplicate_count(records, "url"),
            "title": duplicate_count(records, "title"),
            "article_id": duplicate_count(records, "article_id"),
        },
        "validation": {
            "json_records_valid": True,
            "schema_valid": schema["schema_matches_expected"],
            "all_expected_fields_present": all(c == len(records) for c in completeness.values()),
            "duplicate_urls": duplicate_count(records, "url"),
            "duplicate_titles": duplicate_count(records, "title"),
            "duplicate_article_ids": duplicate_count(records, "article_id"),
        },
    }


def main() -> None:
    # Điểm thực thi chính tạo tập tin manifest
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {RAW_FILE}")
    records = load_records(RAW_FILE)
    manifest = build_manifest(records)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with MANIFEST_FILE.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)
    print(f"Manifest created successfully: {MANIFEST_FILE} (SHA-256: {manifest['dataset']['sha256']})")


if __name__ == "__main__":
    main()