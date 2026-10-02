from __future__ import annotations

import json
import logging
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
import sys
from urllib.parse import urlparse
from src.crawler.crawler import ARTICLE_OUTPUT

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger(__name__)

EXPECTED_FIELDS = [
    "url", "title", "description", "content", "author", "publisher",
    "published_at", "category", "subcategory", "article_id", "crawled_at", "source",
]
NONEMPTY_FIELDS = [
    "url", "title", "description", "content", "publisher",
    "published_at", "category", "crawled_at", "source",
]
TARGET_CATEGORIES = [
    "Thời sự", "Kinh doanh", "Bất động sản", "Khoa học công nghệ", "Sức khỏe",
]
SUSPICIOUS_AUTHORS = {"VnExpress", "VnExpress.net", "vnexpress"}


def load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    # Tải các dòng dữ liệu từ tệp JSONL và bắt lỗi cú pháp nếu có
    records: list[dict] = []
    errors: list[str] = []
    if not path.exists():
        errors.append(f"File does not exist: {path}")
        return records, errors
    with path.open("r", encoding="utf-8") as file:
        for line_num, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    errors.append(f"Line {line_num}: JSON is not object")
                    continue
                records.append(record)
            except json.JSONDecodeError as exc:
                errors.append(f"Line {line_num}: {exc}")
    return records, errors


def count_empty_fields(records: list[dict]) -> Counter[str]:
    # Đếm số lượng trường bắt buộc bị rỗng hoặc thiếu
    empty_counts: Counter[str] = Counter()
    for record in records:
        for field in NONEMPTY_FIELDS:
            value = record.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                empty_counts[field] += 1
    return empty_counts


def find_duplicate_urls(records: list[dict]) -> list[str]:
    # Tìm kiếm các URL bài viết xuất hiện nhiều hơn 1 lần
    counter = Counter(r.get("url") for r in records if r.get("url"))
    return [url for url, count in counter.items() if count > 1]


def schema_issues(records: list[dict]) -> list[dict]:
    # Kiểm tra tính khớp nối của các trường so với schema mong đợi
    issues = []
    expected = set(EXPECTED_FIELDS)
    for index, record in enumerate(records, start=1):
        actual = set(record)
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing or extra:
            issues.append({"record_index": index, "article_id": record.get("article_id"), "missing": missing, "extra": extra})
    return issues


def find_duplicate_values(records: list[dict], field: str) -> dict[str, int]:
    # Đếm số lượng giá trị trùng lặp của một trường cụ thể
    counter = Counter()
    for record in records:
        val = record.get(field)
        if val is not None and str(val).strip():
            counter[str(val).strip()] += 1
    return {val: count for val, count in counter.items() if count > 1}


def timestamp_issues(records: list[dict], field: str) -> list[dict]:
    # Kiểm tra định dạng thời gian ISO 8601 hợp lệ
    issues = []
    for index, record in enumerate(records, start=1):
        val = record.get(field)
        if not val:
            continue
        try:
            datetime.fromisoformat(str(val).replace("Z", "+00:00"))
        except ValueError:
            issues.append({"record_index": index, "article_id": record.get("article_id"), "value": val})
    return issues


def invalid_urls(records: list[dict]) -> list[dict]:
    # Xác thực các URL phải thuộc tên miền VnExpress
    issues = []
    for index, record in enumerate(records, start=1):
        url = record.get("url")
        parsed = urlparse(str(url)) if url else None
        host = parsed.hostname.lower() if parsed and parsed.hostname else ""
        if not host or not (host == "vnexpress.net" or host.endswith(".vnexpress.net")):
            issues.append({"record_index": index, "article_id": record.get("article_id"), "url": url})
    return issues


def get_category_distribution(records: list[dict]) -> Counter[str]:
    # Thống kê phân bố bài viết theo chuyên mục
    return Counter(r.get("category", "UNKNOWN") for r in records)


def get_content_lengths(records: list[dict]) -> list[int]:
    # Lấy độ dài số ký tự phần thân của toàn bộ bài viết
    return [len(r.get("content")) for r in records if isinstance(r.get("content"), str)]


def calculate_content_statistics(lengths: list[int]) -> dict[str, float | int | None]:
    # Tính các chỉ số thống kê độ dài nội dung (min, max, mean, median)
    if not lengths:
        return {"min": None, "max": None, "mean": None, "median": None}
    return {
        "min": min(lengths),
        "max": max(lengths),
        "mean": statistics.mean(lengths),
        "median": statistics.median(lengths),
    }


def find_suspicious_authors(records: list[dict]) -> Counter[str]:
    # Phát hiện các giá trị tác giả nghi vấn mang tên tòa soạn
    suspicious: Counter[str] = Counter()
    for record in records:
        author = record.get("author")
        if isinstance(author, str) and author.strip() in SUSPICIOUS_AUTHORS:
            suspicious[author.strip()] += 1
    return suspicious


def find_suspicious_content(records: list[dict]) -> list[dict]:
    # Phát hiện nội dung bài viết quá ngắn hoặc rỗng
    suspicious: list[dict] = []
    for record in records:
        content = record.get("content", "")
        if not isinstance(content, str) or not content.strip():
            suspicious.append({"url": record.get("url"), "reason": "empty or non-string content"})
        elif len(content.strip()) < 200:
            suspicious.append({"url": record.get("url"), "reason": f"very short content ({len(content.strip())} chars)"})
    return suspicious


def print_report(records: list[dict], json_errors: list[str]) -> None:
    # In báo cáo tổng hợp kiểm định chất lượng dữ liệu thô
    print("\n" + "=" * 70 + "\nRAW DATA VALIDATION\n" + "=" * 70)
    print(f"File: {ARTICLE_OUTPUT} | Articles: {len(records)} | JSON errors: {len(json_errors)}")

    empty_counts = count_empty_fields(records)
    for field in NONEMPTY_FIELDS:
        cnt = empty_counts.get(field, 0)
        print(f"  {field:<18} : {cnt:<5} [{'OK' if cnt == 0 else 'WARNING'}]")

    dup_urls = find_duplicate_urls(records)
    print(f"Duplicate URLs    : {len(dup_urls)}")

    cat_counts = get_category_distribution(records)
    for cat in TARGET_CATEGORIES:
        print(f"  {cat:<25} : {cat_counts.get(cat, 0)}")

    lengths = get_content_lengths(records)
    stats = calculate_content_statistics(lengths)
    print(f"Content stats: min={stats['min']}, max={stats['max']}, mean={stats['mean']:.1f}, median={stats['median']}")

    critical = (len(json_errors) + len(dup_urls) + len(schema_issues(records)) +
                len(find_duplicate_values(records, "title")) + len(timestamp_issues(records, "published_at")) +
                len(invalid_urls(records)) + sum(empty_counts.values()))
    print("=" * 70)
    print("RESULT: PASS" if critical == 0 else "RESULT: REVIEW REQUIRED")
    print("=" * 70 + "\n")


def main() -> None:
    # Điểm thực thi chính kiểm định dữ liệu thô
    records, json_errors = load_jsonl(ARTICLE_OUTPUT)
    print_report(records=records, json_errors=json_errors)


if __name__ == "__main__":
    main()