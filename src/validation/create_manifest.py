"""Module tạo và quản lý biên bản kiểm định tập dữ liệu (Dataset Manifest).
Tính toán mã băm SHA-256 để đóng băng tập dữ liệu thô, kiểm tra tính đầy đủ của schema
và bảo đảm tính toàn vẹn dữ liệu trong suốt chu trình phân tích.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils import (
    EXPECTED_FIELDS,
    OUTPUTS_DIR,
    RAW_DATA_PATH,
    calculate_sha256,
    load_jsonl,
    save_json,
)

REPORT_DIR = OUTPUTS_DIR
MANIFEST_FILE = REPORT_DIR / "dataset_manifest.json"
EXPECTED_SCHEMA = EXPECTED_FIELDS


def load_records(path: Path) -> list[dict[str, Any]]:
    """Đọc danh sách bản ghi JSONL mà không làm thay đổi tệp gốc."""
    return load_jsonl(path)


def inspect_schema(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Xác thực cấu trúc schema chuẩn trên từng bản ghi."""
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

    all_expected_present = expected_fields.issubset(actual_union)
    schema_matches = (
        not records_with_missing_fields
        and not records_with_unexpected_fields
        and all_expected_present
    )

    return {
        "expected_fields": sorted(expected_fields),
        "actual_fields": sorted(actual_union),
        "missing_fields": sorted(expected_fields - actual_union),
        "unexpected_fields": sorted(actual_union - expected_fields),
        "records_with_missing_fields": records_with_missing_fields,
        "records_with_unexpected_fields": records_with_unexpected_fields,
        "schema_matches_expected": schema_matches,
    }


def field_completeness(records: list[dict[str, Any]]) -> dict[str, int]:
    """Đếm số lượng giá trị không rỗng của từng trường dữ liệu."""
    counts: dict[str, int] = {f: 0 for f in EXPECTED_SCHEMA}
    for record in records:
        for field in EXPECTED_SCHEMA:
            val = record.get(field)
            if val is not None and not (isinstance(val, str) and not val.strip()):
                counts[field] += 1
    return counts


def generate_manifest(raw_path: Path = RAW_DATA_PATH) -> dict[str, Any]:
    """Tạo biên bản manifest đóng băng dữ liệu thô với mã băm SHA-256."""
    records = load_records(raw_path)
    file_size = raw_path.stat().st_size if raw_path.exists() else 0
    sha_hash = calculate_sha256(raw_path)
    schema_report = inspect_schema(records)

    manifest = {
        "manifest_version": "1.0",
        "dataset": {
            "name": "ADY201m Raw Dataset v1",
            "path": str(raw_path.relative_to(raw_path.parents[2])),
            "format": "JSONL",
            "source": "VnExpress",
            "records": len(records),
            "file_size_bytes": file_size,
            "sha256": sha_hash,
        },
        "created_at": datetime.now().isoformat(),
        "schema": schema_report,
        "field_completeness": field_completeness(records),
        "category_distribution": dict(Counter(str(r.get("category")) for r in records)),
        "subcategory_distribution": dict(Counter(str(r.get("subcategory")) for r in records)),
        "duplicates": {
            "url": len(records) - len({r.get("url") for r in records if r.get("url")}),
            "title": len(records) - len({r.get("title") for r in records if r.get("title")}),
            "article_id": len(records) - len({r.get("article_id") for r in records if r.get("article_id")}),
        },
        "validation": {
            "json_records_valid": len(records) > 0,
            "schema_valid": schema_report["schema_matches_expected"],
            "all_expected_fields_present": len(schema_report["missing_fields"]) == 0,
        },
    }

    save_json(MANIFEST_FILE, manifest)
    return manifest


def main() -> None:
    """Khởi chạy tạo manifest từ dòng lệnh."""
    manifest = generate_manifest()
    print("=" * 60)
    print("BIÊN BẢN DATASET MANIFEST ĐÃ ĐƯỢC TẠO")
    print(f"Số lượng bản ghi: {manifest['dataset']['records']}")
    print(f"Mã băm SHA-256:   {manifest['dataset']['sha256']}")
    print("=" * 60)


if __name__ == "__main__":
    main()