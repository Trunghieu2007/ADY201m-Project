"""Module tự động tổ chức chuyên mục, chuẩn hóa phân loại và trích xuất từ khóa xu hướng.
Áp dụng kỹ thuật thống kê tần suất từ vựng và bộ lọc stopwords tiếng Việt (Knowledge.md).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from src.utils import (
    CANONICAL_CATEGORIES,
    CATEGORY_SUMMARY_PATH,
    PROCESSED_DATA_PATH,
    RAW_DATA_PATH,
    STOPWORDS,
    load_json,
    load_jsonl,
    save_json,
)

ROOT = RAW_DATA_PATH.parents[2]
RAW_PATH = RAW_DATA_PATH
PROCESSED_PATH = PROCESSED_DATA_PATH
SUMMARY_PATH = CATEGORY_SUMMARY_PATH


def extract_category_from_url(url: str) -> str:
    """Trích xuất tên danh mục chuẩn từ slug đường dẫn URL của bài viết VnExpress."""
    match = re.search(r"vnexpress\.net/([^/]+)", url)
    if match:
        slug = match.group(1).lower()
        return CANONICAL_CATEGORIES.get(slug, slug.replace("-", " ").title())
    return "Thời sự"


def organize_articles(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Phân nhóm bài viết tự động theo tên danh mục chuẩn hóa."""
    organized: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        cat = r.get("category") or extract_category_from_url(r.get("url", ""))
        organized.setdefault(cat, []).append(r)
    return organized


def get_top_keywords(records: list[dict[str, Any]], top_n: int = 10) -> list[tuple[str, int]]:
    """Thống kê top từ khóa xuất hiện nhiều nhất sau khi lọc bỏ stopwords tiếng Việt."""
    words = [
        w
        for r in records
        for w in re.findall(r"\b[A-Za-zÀ-ỹ0-9_]{3,}\b", (r.get("content") or r.get("title") or "").lower())
        if w not in STOPWORDS and not w.isdigit()
    ]
    return Counter(words).most_common(top_n)


def compute_category_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Tổng hợp các chỉ số định lượng và từ khóa đại diện cho từng danh mục."""
    organized = organize_articles(records)
    total = len(records)
    return {
        "total_articles": total,
        "total_categories": len(organized),
        "categories": {
            cat: {
                "count": len(items),
                "percentage": round((len(items) / total) * 100, 1) if total else 0,
                "average_word_count": round(sum(wc) / len(wc), 1) if (wc := [len(item.get("content", "").split()) for item in items]) else 0,
                "subcategories": dict(Counter(item.get("subcategory") or cat for item in items)),
                "authors": dict(Counter(item.get("author") or "Unknown" for item in items)),
                "top_keywords": get_top_keywords(items, top_n=8),
            }
            for cat, items in organized.items()
        },
    }


def validate_summary(path: Path = SUMMARY_PATH) -> dict[str, Any]:
    """Tự kiểm định tính toàn vẹn của tệp category_summary.json trên đĩa."""
    if not path.exists():
        return {"result": "FAIL", "error": f"Không tìm thấy tệp {path}"}
    try:
        data = load_json(path)
        if data.get("total_articles", 0) < 20 or data.get("total_categories", 0) < 5:
            return {"result": "FAIL", "error": "Số lượng bài viết hoặc chuyên mục không đủ chuẩn (yêu cầu >= 20 bài, 5 chuyên mục)"}
        return {"result": "PASS", "articles": data["total_articles"], "categories": data["total_categories"]}
    except Exception as exc:
        return {"result": "FAIL", "error": str(exc)}


def run_organization() -> dict[str, Any]:
    """Thực thi tự động tổ chức danh mục và lưu tệp JSON tổng hợp."""
    source_path = PROCESSED_PATH if PROCESSED_PATH.exists() else RAW_PATH
    if not source_path.exists():
        raise FileNotFoundError(f"Input dataset not found at {source_path}")
    records = load_jsonl(source_path)
    summary = compute_category_summary(records)
    save_json(SUMMARY_PATH, summary)
    return summary


def main() -> None:
    """Entrypoint dòng lệnh thực thi tổ chức chuyên mục và tự kiểm định."""
    parser = argparse.ArgumentParser(description="Tự động tổ chức chuyên mục & khám phá từ khóa xu hướng")
    parser.add_argument("--check", action="store_true", help="Chỉ kiểm định tính hợp lệ của tệp category_summary.json")
    args = parser.parse_args()

    if args.check:
        res = validate_summary()
        print(json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(0 if res.get("result") == "PASS" else 1)

    res = run_organization()
    val = validate_summary()
    print(f"Tổ chức danh mục hoàn tất: {val.get('result', 'PASS')} ({res['total_articles']} bài, {res['total_categories']} chuyên mục)")
    sys.exit(0 if val.get("result") == "PASS" else 1)


if __name__ == "__main__":
    main()
