"""Module kiểm định chất lượng kỹ thuật của tập dữ liệu thô (Phase E - Ingestion Validation).
Kiểm tra cấu trúc 12 trường schema, tính duy nhất của URL, định dạng thời gian ISO 8601
và tính toàn vẹn của nội dung theo chuẩn tri thức Knowledge.md.
"""
from __future__ import annotations

import logging
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from src.utils import (
    EXPECTED_FIELDS,
    NONEMPTY_FIELDS,
    RAW_DATA_PATH,
    TARGET_CATEGORIES,
    describe_numeric,
    load_jsonl,
)

logger = logging.getLogger(__name__)

ARTICLE_OUTPUT = RAW_DATA_PATH
SUSPICIOUS_AUTHORS = {"VnExpress", "VnExpress.net", "vnexpress"}


def count_empty_fields(records: list[dict]) -> Counter[str]:
    """Đếm số lượng trường bắt buộc bị thiếu hoặc rỗng (bỏ qua các trường nullable)."""
    counter: Counter[str] = Counter()
    for record in records:
        for field in NONEMPTY_FIELDS:
            value = record.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                counter[field] += 1
    return counter


def find_duplicate_values(records: list[dict], field: str) -> list[str]:
    """Tìm các giá trị xuất hiện lặp lại nhiều hơn 1 lần của một trường cụ thể."""
    counts = Counter(
        record.get(field)
        for record in records
        if record.get(field) and str(record.get(field)).strip()
    )
    return [val for val, count in counts.items() if count > 1]


def find_duplicate_urls(records: list[dict]) -> list[str]:
    """Tìm kiếm các URL bài viết xuất hiện nhiều hơn 1 lần trong tập dữ liệu."""
    return find_duplicate_values(records, "url")


def schema_issues(records: list[dict]) -> list[dict]:
    """Kiểm tra sự khớp nối giữa các trường trong từng bản ghi với schema mong đợi."""
    expected_set = set(EXPECTED_FIELDS)
    issues = []
    for line_num, record in enumerate(records, start=1):
        actual_set = set(record.keys())
        missing = sorted(expected_set - actual_set)
        extra = sorted(actual_set - expected_set)
        if missing or extra:
            issues.append({"record_index": line_num, "missing": missing, "extra": extra})
    return issues


def timestamp_issues(records: list[dict], field: str) -> list[dict]:
    """Kiểm tra định dạng thời gian ISO 8601 hợp lệ của trường timestamp."""
    issues = []
    for line_num, record in enumerate(records, start=1):
        val = record.get(field)
        if not val or not isinstance(val, str):
            issues.append({"record_index": line_num, "field": field, "value": val, "reason": "empty or not string"})
            continue
        try:
            datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError as exc:
            issues.append({"record_index": line_num, "field": field, "value": val, "reason": str(exc)})
    return issues


def invalid_urls(records: list[dict]) -> list[dict]:
    """Xác thực đường dẫn URL: bắt buộc có scheme http/https và thuộc tên miền vnexpress.net."""
    issues = []
    for line_num, record in enumerate(records, start=1):
        raw_url = record.get("url")
        if not raw_url:
            issues.append({"record_index": line_num, "url": raw_url, "reason": "missing"})
            continue
        parsed = urlparse(raw_url)
        if parsed.scheme not in {"http", "https"}:
            issues.append({"record_index": line_num, "url": raw_url, "reason": f"invalid scheme {parsed.scheme}"})
        elif "vnexpress.net" not in (parsed.netloc or ""):
            issues.append({"record_index": line_num, "url": raw_url, "reason": f"external domain {parsed.netloc}"})
    return issues


def get_content_lengths(records: list[dict]) -> list[int]:
    """Lấy danh sách độ dài ký tự của nội dung thân bài viết."""
    return [len(str(record.get("content") or "")) for record in records if record.get("content")]


def calculate_content_statistics(lengths: list[int]) -> dict:
    """Tính các chỉ số thống kê mô tả phân phối độ dài bài viết."""
    return describe_numeric(lengths)


def get_category_distribution(records: list[dict]) -> dict[str, int]:
    """Thống kê tần suất số lượng bài viết phân bổ theo từng chuyên mục."""
    return dict(Counter(record.get("category") or "(missing)" for record in records))


def find_suspicious_authors(records: list[dict]) -> list[dict]:
    """Phát hiện các tên tác giả có dấu hiệu rò rỉ tên tòa soạn."""
    findings = []
    for line_num, record in enumerate(records, start=1):
        author = record.get("author")
        if author and author.strip() in SUSPICIOUS_AUTHORS:
            findings.append({"record_index": line_num, "author": author})
    return findings


def find_suspicious_content(records: list[dict]) -> list[dict]:
    """Phát hiện các bài viết có nội dung quá ngắn dưới 100 ký tự."""
    findings = []
    for line_num, record in enumerate(records, start=1):
        content = record.get("content") or ""
        if len(content.strip()) < 100:
            findings.append({"record_index": line_num, "char_count": len(content.strip())})
    return findings


def load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    """Tải dữ liệu từ tệp JSON hoặc JSONL và bắt lỗi cú pháp nếu có."""
    import json
    records, errors = [], []
    target_path = path
    if not target_path.exists():
        alt = target_path.with_suffix(".json") if target_path.suffix == ".jsonl" else target_path.with_suffix(".jsonl")
        if alt.exists():
            target_path = alt
        else:
            errors.append(f"Tệp không tồn tại: {path}")
            return records, errors

    if target_path.suffix == ".json":
        try:
            with target_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, list):
                    for idx, item in enumerate(data, start=1):
                        if isinstance(item, dict):
                            records.append(item)
                        else:
                            errors.append(f"Bản ghi {idx}: JSON không phải object")
                elif isinstance(data, dict):
                    records.append(data)
                else:
                    errors.append("Tệp JSON không chứa danh sách hoặc đối tượng hợp lệ")
        except json.JSONDecodeError as exc:
            errors.append(f"Lỗi cú pháp JSON: {exc}")
        return records, errors

    with target_path.open("r", encoding="utf-8") as file:
        for line_num, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    errors.append(f"Dòng {line_num}: JSON không phải object")
                    continue
                records.append(record)
            except json.JSONDecodeError as exc:
                errors.append(f"Dòng {line_num}: {exc}")
    return records, errors



def print_report(records: list[dict], errors: list[str]) -> bool:
    """In báo cáo kiểm định chất lượng dữ liệu thô tổng thể ra console."""
    print("=" * 60)
    print("BÁO CÁO KIỂM ĐỊNH CHẤT LƯỢNG DỮ LIỆU THÔ (RAW DATA VALIDATION)")
    print("=" * 60)
    print(f"Tổng số bản ghi đọc được: {len(records)}")
    if errors:
        print(f"[CẢNH BÁO] Có {len(errors)} lỗi cú pháp khi nạp dữ liệu.")
    empty_fields = count_empty_fields(records)
    print(f"Trường bắt buộc bị rỗng: {dict(empty_fields) if empty_fields else 'Không có (100% đầy đủ)'}")
    dup_urls = find_duplicate_urls(records)
    print(f"URL trùng lặp: {len(dup_urls)}")
    cat_dist = get_category_distribution(records)
    print(f"Phân bổ chuyên mục: {cat_dist}")
    content_stats = calculate_content_statistics(get_content_lengths(records))
    print(f"Thống kê số ký tự: Trung bình={content_stats.get('mean')}, Min={content_stats.get('min')}, Max={content_stats.get('max')}")
    print("=" * 60)
    return len(errors) == 0 and len(empty_fields) == 0 and len(dup_urls) == 0


def main(path: Path = ARTICLE_OUTPUT) -> int:
    """Điểm khởi chạy kiểm định dữ liệu thô từ dòng lệnh."""
    records, errors = load_jsonl(path)
    success = print_report(records, errors)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())