from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "data" / "raw" / "articles.jsonl"
PROCESSED_PATH = ROOT / "data" / "processed" / "articles_processed.jsonl"
SUMMARY_PATH = ROOT / "data" / "processed" / "category_summary.json"

CANONICAL_CATEGORIES = {
    "thoi-su": "Thời sự",
    "kinh-doanh": "Kinh doanh",
    "bat-dong-san": "Bất động sản",
    "khoa-hoc": "Khoa học công nghệ",
    "khoa-hoc-cong-nghe": "Khoa học công nghệ",
    "suc-khoe": "Sức khỏe",
}

STOPWORDS = {
    "và", "của", "là", "có", "cho", "trong", "được", "các", "với", "những",
    "đã", "khi", "người", "đến", "ở", "này", "về", "một", "để", "ra",
    "sau", "từ", "theo", "nhiều", "hơn", "không", "sẽ", "như", "lại", "vào",
    "cũng", "đang", "tại", "biết", "lên", "trên", "phải", "ngày", "bị", "rồi",
    "rất", "nói", "hay", "còn", "thì", "làm", "nhưng", "qua", "do", "gần",
}


# Trích xuất tên danh mục chuẩn từ slug đường dẫn URL của bài viết VnExpress
def extract_category_from_url(url: str) -> str:
    match = re.search(r"vnexpress\.net/([^/]+)", url)
    if match:
        slug = match.group(1).lower()
        return CANONICAL_CATEGORIES.get(slug, slug.replace("-", " ").title())
    return "Thời sự"


# Phân nhóm bài viết tự động theo tên danh mục chuẩn hóa
def organize_articles(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    organized: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        cat = record.get("category") or extract_category_from_url(record.get("url", ""))
        organized.setdefault(cat, []).append(record)
    return organized


# Thống kê top từ khóa xuất hiện nhiều nhất sau khi lọc bỏ stopwords tiếng Việt
def get_top_keywords(records: list[dict[str, Any]], top_n: int = 10) -> list[tuple[str, int]]:
    words: list[str] = []
    for record in records:
        text = record.get("content", "") or record.get("title", "")
        clean_words = re.findall(r"\b[A-Za-zÀ-ỹ0-9_]{3,}\b", text.lower())
        for w in clean_words:
            if w not in STOPWORDS and not w.isdigit():
                words.append(w)
    return Counter(words).most_common(top_n)


# Tổng hợp các chỉ số định lượng và từ khóa đại diện cho từng danh mục
def compute_category_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    organized = organize_articles(records)
    summary: dict[str, Any] = {
        "total_articles": len(records),
        "total_categories": len(organized),
        "categories": {},
    }
    for cat_name, items in organized.items():
        subcategories = Counter([item.get("subcategory") or cat_name for item in items])
        authors = Counter([item.get("author") or "Unknown" for item in items])
        word_counts = [len(item.get("content", "").split()) for item in items]
        summary["categories"][cat_name] = {
            "count": len(items),
            "percentage": round((len(items) / len(records)) * 100, 1) if records else 0,
            "average_word_count": round(sum(word_counts) / len(word_counts), 1) if word_counts else 0,
            "subcategories": dict(subcategories),
            "authors": dict(authors),
            "top_keywords": get_top_keywords(items, top_n=8),
        }
    return summary


# Thực thi tự động tổ chức danh mục và lưu tệp JSON tổng hợp
def run_organization() -> dict[str, Any]:
    source_path = PROCESSED_PATH if PROCESSED_PATH.exists() else RAW_PATH
    if not source_path.exists():
        raise FileNotFoundError(f"Input dataset not found at {source_path}")
    records = []
    with source_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    summary = compute_category_summary(records)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    res = run_organization()
    print(f"Successfully organized {res['total_articles']} articles into {res['total_categories']} categories.")
