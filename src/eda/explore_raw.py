from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FILE = PROJECT_ROOT / "data" / "raw" / "articles.jsonl"
EDA_DIR = PROJECT_ROOT / "outputs" / "eda"
OVERVIEW_FILE = EDA_DIR / "dataset_overview.json"
SUMMARY_FILE = EDA_DIR / "eda_summary.txt"
CONTENT_LENGTH_CHART = EDA_DIR / "content_length.png"
CATEGORY_CHART = EDA_DIR / "category_distribution.png"

DATASET_FIELDS = [
    "url", "title", "description", "content", "author", "publisher",
    "published_at", "category", "subcategory", "article_id", "crawled_at", "source",
]


# Đọc danh sách bài viết từ file JSONL ở chế độ chỉ đọc
def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"WARNING: invalid JSON at line {line_no}: {exc}")
                continue
            if not isinstance(record, dict):
                print(f"WARNING: line {line_no} is not an object")
                continue
            records.append(record)
    return records


# Tính độ dài ký tự của một giá trị sau khi strip
def text_length(value: Any) -> int:
    return len(str(value).strip()) if value is not None else 0


# Kiểm tra xem trường dữ liệu có bị null hoặc chuỗi rỗng hay không
def field_missing(record: dict[str, Any], field: str) -> bool:
    val = record.get(field)
    return val is None or (isinstance(val, str) and not val.strip())


# Tính toán thống kê mô tả số học (min, max, mean, median)
def _calc_stats(values: list[int]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": 0, "max": 0, "mean": 0, "median": 0}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
    }


# Tổng hợp các chỉ số thống kê EDA tổng quan cho tập dữ liệu raw
def dataset_overview(records: list[dict[str, Any]]) -> dict[str, Any]:
    def _extract_nonempty(field: str) -> list[str]:
        return [str(r.get(field, "")).strip() for r in records if str(r.get(field, "")).strip()]

    titles = [str(r.get("title", "")).strip() for r in records]
    contents = [str(r.get("content", "")).strip() for r in records]
    categories = _extract_nonempty("category")
    subcategories = _extract_nonempty("subcategory")
    authors = _extract_nonempty("author")
    publishers = _extract_nonempty("publisher")
    published_dates = _extract_nonempty("published_at")
    crawled_dates = _extract_nonempty("crawled_at")
    sources = _extract_nonempty("source")
    article_ids = _extract_nonempty("article_id")
    urls = _extract_nonempty("url")

    content_lengths = [len(c) for c in contents if c]
    title_lengths = [len(t) for t in titles if t]
    description_lengths = [text_length(r.get("description")) for r in records]

    missing_fields = {f: sum(field_missing(r, f) for r in records) for f in DATASET_FIELDS}
    cat_counter = Counter(categories)
    subcat_counter = Counter(subcategories)

    titles_clean = [t for t in titles if t]
    dup_urls = len(urls) - len(set(urls))
    dup_titles = len(titles_clean) - len(set(titles_clean))
    dup_ids = len(article_ids) - len(set(article_ids))

    return {
        "dataset": str(RAW_FILE.relative_to(PROJECT_ROOT)),
        "records": len(records),
        "schema": {"fields": DATASET_FIELDS, "field_count": len(DATASET_FIELDS)},
        "category_count": len(cat_counter),
        "categories": dict(cat_counter),
        "subcategory_count": len(subcat_counter),
        "subcategories": dict(subcat_counter),
        "authors_present": len(authors),
        "publishers_present": len(publishers),
        "published_dates_present": len(published_dates),
        "crawled_dates_present": len(crawled_dates),
        "sources_present": len(sources),
        "article_ids_present": len(article_ids),
        "missing_fields": missing_fields,
        "duplicates": {
            "duplicate_urls": dup_urls,
            "duplicate_titles": dup_titles,
            "duplicate_article_ids": dup_ids,
        },
        "content_length": _calc_stats(content_lengths),
        "title_length": _calc_stats(title_lengths),
        "description_length": _calc_stats(description_lengths),
    }


# Vẽ biểu đồ phân phối độ dài nội dung bài viết
def create_content_length_chart(records: list[dict[str, Any]]) -> None:
    lengths = [text_length(r.get("content")) for r in records]
    lengths = [l for l in lengths if l > 0]
    if not lengths:
        return
    plt.figure(figsize=(10, 6))
    plt.hist(lengths, bins=min(10, max(1, len(lengths))))
    plt.title("Article Content Length Distribution")
    plt.xlabel("Content length (characters)")
    plt.ylabel("Number of articles")
    plt.tight_layout()
    plt.savefig(CONTENT_LENGTH_CHART, dpi=150)
    plt.close()


# Vẽ biểu đồ cột phân phối số lượng bài viết theo danh mục
def create_category_chart(records: list[dict[str, Any]]) -> None:
    categories = [str(r.get("category", "")).strip() for r in records if str(r.get("category", "")).strip()]
    counts = Counter(categories)
    if not counts:
        return
    plt.figure(figsize=(10, 6))
    plt.bar(list(counts.keys()), list(counts.values()))
    plt.title("Article Distribution by Category")
    plt.xlabel("Category")
    plt.ylabel("Number of articles")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(CATEGORY_CHART, dpi=150)
    plt.close()


# Tạo báo cáo tóm tắt EDA định dạng văn bản
def build_summary(overview: dict[str, Any]) -> str:
    content, title, desc = overview["content_length"], overview["title_length"], overview["description_length"]
    missing, categories, dups = overview["missing_fields"], overview["categories"], overview["duplicates"]
    lines = [
        "ADY201m - RAW DATASET EDA", "=" * 60, "",
        f"Dataset:\n  {overview['dataset']}", "",
        f"Schema:\n  Field count: {overview['schema']['field_count']}\n  Fields:",
    ]
    for field in overview["schema"]["fields"]:
        lines.append(f"    - {field}")
    lines.extend([
        "", f"Dataset size:\n  Articles: {overview['records']}\n  Categories: {overview['category_count']}\n  Subcategories: {overview['subcategory_count']}",
        "", "Category distribution:",
    ])
    for cat, count in categories.items():
        lines.append(f"  - {cat}: {count}")
    lines.extend([
        "", "Presence of metadata:",
        f"  Authors:         {overview['authors_present']}",
        f"  Publishers:      {overview['publishers_present']}",
        f"  Published dates: {overview['published_dates_present']}",
        f"  Crawled dates:   {overview['crawled_dates_present']}",
        f"  Sources:         {overview['sources_present']}",
        f"  Article IDs:     {overview['article_ids_present']}",
        "", f"Content length:\n  Minimum: {content['min']}\n  Maximum: {content['max']}\n  Mean:    {content['mean']}\n  Median:  {content['median']}",
        "", f"Title length:\n  Minimum: {title['min']}\n  Maximum: {title['max']}\n  Mean:    {title['mean']}\n  Median:  {title['median']}",
        "", f"Description length:\n  Minimum: {desc['min']}\n  Maximum: {desc['max']}\n  Mean:    {desc['mean']}\n  Median:  {desc['median']}",
        "", "Missing fields:",
    ])
    for f, c in missing.items():
        lines.append(f"  - {f}: {c}")
    lines.extend([
        "", "Duplicate records:",
        f"  Duplicate URLs:       {dups['duplicate_urls']}",
        f"  Duplicate titles:     {dups['duplicate_titles']}",
        f"  Duplicate article IDs:{dups['duplicate_article_ids']}",
        "", "IMPORTANT:\n  This EDA reads the raw dataset only.\n  No cleaning or modification was performed.",
    ])
    return "\n".join(lines)


# Hàm thực thi chính cho script EDA raw dataset
def main() -> None:
    print("ADY201m - Raw Dataset EDA\n" + "=" * 60 + f"\nInput: {RAW_FILE}")
    records = load_jsonl(RAW_FILE)
    print(f"Loaded records: {len(records)}")
    overview = dataset_overview(records)
    EDA_DIR.mkdir(parents=True, exist_ok=True)
    with OVERVIEW_FILE.open("w", encoding="utf-8") as file:
        json.dump(overview, file, ensure_ascii=False, indent=2)
    with SUMMARY_FILE.open("w", encoding="utf-8") as file:
        file.write(build_summary(overview))
    create_content_length_chart(records)
    create_category_chart(records)
    print(f"\nEDA COMPLETE\n" + "-" * 60)
    print(f"Articles:   {overview['records']}\nCategories: {overview['category_count']}")
    print(f"Mean content length: {overview['content_length']['mean']}\nMedian content length: {overview['content_length']['median']}")
    print(f"\nJSON report: {OVERVIEW_FILE}\nTXT report:  {SUMMARY_FILE}\nChart:       {CONTENT_LENGTH_CHART}\nChart:       {CATEGORY_CHART}")


if __name__ == "__main__":
    main()