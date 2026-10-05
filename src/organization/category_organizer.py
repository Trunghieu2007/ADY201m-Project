"""Module tự động tổ chức chuyên mục, chuẩn hóa phân loại và trích xuất từ khóa xu hướng."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

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
    for r in records:
        cat = r.get("category") or extract_category_from_url(r.get("url", ""))
        organized.setdefault(cat, []).append(r)
    return organized


# Thống kê top từ khóa xuất hiện nhiều nhất sau khi lọc bỏ stopwords tiếng Việt
def get_top_keywords(records: list[dict[str, Any]], top_n: int = 10) -> list[tuple[str, int]]:
    words = [
        w
        for r in records
        for w in re.findall(r"\b[A-Za-zÀ-ỹ0-9_]{3,}\b", (r.get("content") or r.get("title") or "").lower())
        if w not in STOPWORDS and not w.isdigit()
    ]
    return Counter(words).most_common(top_n)


# Tổng hợp các chỉ số định lượng và từ khóa đại diện cho từng danh mục
def compute_category_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
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


# Tự kiểm định tính toàn vẹn của tệp category_summary.json trên đĩa
def validate_summary(path: Path = SUMMARY_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"result": "FAIL", "error": f"Không tìm thấy tệp {path}"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("total_articles") != 20 or data.get("total_categories") < 5:
            return {"result": "FAIL", "error": "Số lượng bài viết hoặc chuyên mục không đủ chuẩn"}
        return {"result": "PASS", "articles": data["total_articles"], "categories": data["total_categories"]}
    except Exception as exc:
        return {"result": "FAIL", "error": str(exc)}


# Thực thi tự động tổ chức danh mục và lưu tệp JSON tổng hợp
def run_organization() -> dict[str, Any]:
    source_path = PROCESSED_PATH if PROCESSED_PATH.exists() else RAW_PATH
    if not source_path.exists():
        raise FileNotFoundError(f"Input dataset not found at {source_path}")
    with source_path.open("r", encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle if line.strip()]
    summary = compute_category_summary(records)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


# Điểm khởi chạy chính CLI thực thi tổ chức chuyên mục và tự kiểm định
def main() -> None:
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
