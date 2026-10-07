"""Module tiền xử lý (Preprocessing), chuẩn hóa và tổ chức chuyên mục (Phase T — Transform).
Bảo toàn 100% dữ liệu gốc (Non-destructive Transformation) tuân thủ Knowledge.md:
1. Chuẩn hóa Unicode NFC, làm sạch văn bản, khử lặp tiêu đề và đoạn mở đầu (sapo).
2. Trích xuất 13 đặc trưng mô tả số học (độ dài, số câu, từ vựng, khung giờ, nhịp tuần).
3. Phân bổ chuyên mục, lọc bộ Stopwords tiếng Việt và tìm top từ khóa xu hướng.
4. Xuất các sản phẩm dữ liệu sạch: articles_processed.jsonl, feature_matrix.csv và category_summary.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils import (
    CANONICAL_CATEGORIES,
    CATEGORY_SUMMARY_PATH,
    EXPECTED_FIELDS,
    FEATURE_COLUMNS,
    FEATURE_MATRIX_PATH,
    OUTPUTS_DIR,
    PROCESSED_DATA_PATH,
    RAW_DATA_PATH,
    STOPWORDS,
    load_json,
    load_jsonl,
    save_json,
    save_jsonl,
)

logger = logging.getLogger(__name__)

ROOT = RAW_DATA_PATH.parents[2]
RAW = RAW_DATA_PATH
OUT = PROCESSED_DATA_PATH.parent
REPORTS = OUTPUTS_DIR / "preprocessing"
PROCESSED_OUTPUT = PROCESSED_DATA_PATH
FEATURE_MATRIX_OUTPUT = FEATURE_MATRIX_PATH
MANIFEST_OUTPUT = REPORTS / "phase3_manifest.json"
SUMMARY_PATH = CATEGORY_SUMMARY_PATH

_WHITESPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)

DESCRIPTIVE_FEATURES = list(FEATURE_COLUMNS)
CORE_RAW_FIELDS = tuple(EXPECTED_FIELDS)


# -----------------------------------------------------------------------------
# 1. CÁC HÀM LÀM SẠCH VĂN BẢN & CHUẨN HÓA DỮ LIỆU
# -----------------------------------------------------------------------------

def normalize_unicode(text: str | None) -> str:
    """Chuẩn hóa văn bản tiếng Việt sang bảng mã Unicode dựng sẵn (NFC)."""
    return unicodedata.normalize("NFC", str(text)) if text else ""


def normalize_text(text: str | None) -> str:
    """Loại bỏ URL rác, chuẩn hóa khoảng trắng thừa và ký tự không ngắt."""
    cleaned = _URL_RE.sub(" ", normalize_unicode(text)).replace("\u00a0", " ")
    return _WHITESPACE_RE.sub(" ", cleaned).strip()


def tokenize(text: str | None) -> list[str]:
    """Tách từ cơ bản dựa trên phân tách khoảng trắng."""
    return normalize_text(text).split() if text else []


def sentence_count(text: str | None) -> int:
    """Đếm số câu dựa trên các dấu kết thúc câu (. ! ? …)."""
    t = normalize_text(text)
    return sum(bool(p.strip()) for p in re.split(r"(?<=[.!?…])\s+", t)) if t else 0


def remove_leading_duplicate_blocks(content: str | None, title: str | None = None, description: str | None = None) -> str:
    """Loại bỏ đoạn mở đầu trùng lặp với tiêu đề hoặc mô tả do bóc tách HTML."""
    val, t_n, d_n = normalize_text(content), normalize_text(title), normalize_text(description)
    if not val:
        return ""
    if t_n:
        while val.startswith(t_n + " "):
            val = val[len(t_n):].lstrip()
    if d_n and val.startswith(d_n + " "):
        val = val[len(d_n):].lstrip()
    return val


def lexical_features(text: str | None) -> dict[str, float | int]:
    """Tính toán 6 chỉ số đặc trưng từ vựng cơ bản của chuỗi văn bản."""
    cleaned = normalize_text(text)
    tokens = tokenize(cleaned)
    lengths = [len(re.sub(r"[^\wÀ-ỹĐđ]", "", t, flags=re.UNICODE)) for t in tokens if t]
    lengths = [n for n in lengths if n > 0]
    unique = {t.casefold() for t in tokens}
    return {
        "char_count": len(cleaned),
        "word_count": len(tokens),
        "sentence_count": sentence_count(cleaned),
        "unique_word_count": len(unique),
        "lexical_diversity": round(len(unique) / len(tokens), 6) if tokens else 0.0,
        "avg_word_length": round(sum(lengths) / len(lengths), 6) if lengths else 0.0,
    }


def normalize_author(author: str | None) -> str | None:
    """Chuẩn hóa tên tác giả sang trường phái sinh author_clean, bảo toàn dữ liệu gốc."""
    if author is None:
        return None
    val = re.sub(r"\s+", " ", str(author)).strip()
    val = re.sub(r"\s*\(\s*Tổng hợp\s*\)", " tổng hợp", val, flags=re.I).strip()
    return val or None


def parse_dt(value: str | None) -> datetime | None:
    """Phân tích chuỗi ISO datetime sang datetime object."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


# -----------------------------------------------------------------------------
# 2. TIỀN XỬ LÝ BẢN GHI & MA TRẬN 13 ĐẶC TRƯNG MÔ TẢ
# -----------------------------------------------------------------------------

def preprocess_record(record: dict, category_map: dict[str, int], subcategory_map: dict[str, int]) -> dict:
    """Tiền xử lý văn bản, trích xuất 13 đặc trưng mô tả cho SQL Server, bảo toàn dữ liệu gốc."""
    title, desc = normalize_text(record.get("title")), normalize_text(record.get("description"))
    content_raw = normalize_text(record.get("content"))
    content = remove_leading_duplicate_blocks(content_raw, title, desc)
    c_feat, t_feat, d_feat = lexical_features(content), lexical_features(title), lexical_features(desc)
    dt = parse_dt(record.get("published_at"))

    features = {
        **c_feat,
        "title_char_count": t_feat["char_count"],
        "title_word_count": t_feat["word_count"],
        "description_char_count": d_feat["char_count"],
        "description_word_count": d_feat["word_count"],
        "title_to_content_word_ratio": round(t_feat["word_count"] / c_feat["word_count"], 6) if c_feat["word_count"] else 0.0,
        "category_id": category_map.get(record.get("category", ""), 0),
        "subcategory_id": subcategory_map.get(record.get("subcategory"), 0),
        "publication_hour": dt.hour if dt else -1,
        "publication_weekday": dt.weekday() if dt else -1,
    }

    return {
        **record,
        "processed_text": {
            "title_clean": title, "description_clean": desc, "content_clean": content,
            "content_cleaning": {
                "raw_char_count": len(content_raw), "clean_char_count": len(content),
                "leading_duplicate_removed": len(content) < len(content_raw),
            },
            "combined_text": " ".join(x for x in (title, desc, content) if x),
            "content_tokens": tokenize(content),
        },
        "processed_metadata": {
            "author_clean": normalize_author(record.get("author")),
            "category_id": features["category_id"],
            "subcategory_id": features["subcategory_id"],
        },
        "features": features,
    }


def build_feature_matrix(rows: list[dict]) -> tuple[list[str], list[list[float | int]]]:
    """Xây dựng ma trận 13 đặc trưng mô tả kèm khóa ID chuẩn bị cho nạp CSDL."""
    header = ["article_id", "category_id", "subcategory_id", *DESCRIPTIVE_FEATURES]
    matrix = [[r["article_id"], r["features"]["category_id"], r["features"]["subcategory_id"]] + [r["features"][k] for k in DESCRIPTIVE_FEATURES] for r in rows]
    return header, matrix


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    """Ghi tiêu đề và các hàng dữ liệu ra tệp CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def validate(raw_path: Path = RAW, processed_path: Path = PROCESSED_OUTPUT, feature_path: Path = FEATURE_MATRIX_OUTPUT) -> dict:
    """Kiểm tra tính toàn vẹn, bảo toàn dữ liệu gốc và tính hợp lệ của dữ liệu tiền xử lý."""
    raw, processed = load_jsonl(raw_path), load_jsonl(processed_path)
    errors = []

    if len(raw) != len(processed):
        errors.append(f"Số lượng bản ghi không khớp: raw={len(raw)}, processed={len(processed)}")
    if [r.get("article_id") for r in raw] != [p.get("article_id") for p in processed]:
        errors.append("Thứ tự hoặc mã article_id bị thay đổi sau tiền xử lý")

    for idx, (r, p) in enumerate(zip(raw, processed), start=1):
        for k in CORE_RAW_FIELDS:
            if r.get(k) != p.get(k):
                errors.append(f"Bản ghi {idx}: trường gốc '{k}' bị thay đổi")
        if not p.get("processed_text", {}).get("content_clean") and r.get("content"):
            errors.append(f"Bản ghi {idx}: content_clean bị rỗng")
        f = p.get("features", {})
        for col in DESCRIPTIVE_FEATURES:
            if col not in f or f[col] is None:
                errors.append(f"Bản ghi {idx}: thiếu đặc trưng '{col}'")

    if not feature_path.exists() or len(feature_path.read_text(encoding="utf-8").splitlines()[0].split(",")) < 10:
        errors.append("feature_matrix.csv không hợp lệ hoặc ít hơn 10 cột")

    return {"result": "PASS" if not errors else "FAIL", "records": len(processed), "errors": errors, "features_count": len(DESCRIPTIVE_FEATURES)}


def run_preprocessing(raw_path: Path = RAW) -> dict:
    """Điều phối toàn bộ quy trình Transform: làm sạch, trích xuất đặc trưng và tự kiểm định."""
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    raw_rows = load_jsonl(raw_path)

    categories = sorted({r["category"] for r in raw_rows if r.get("category")})
    subcategories = sorted({r["subcategory"] for r in raw_rows if r.get("subcategory")})
    category_map = {v: i + 1 for i, v in enumerate(categories)}
    subcategory_map = {v: i + 1 for i, v in enumerate(subcategories)}

    processed_rows = [preprocess_record(r, category_map, subcategory_map) for r in raw_rows]
    save_jsonl(PROCESSED_OUTPUT, processed_rows)

    header, matrix = build_feature_matrix(processed_rows)
    write_csv(FEATURE_MATRIX_OUTPUT, header, matrix)

    manifest = {
        "phase": "Phase T — Data Cleaning & Descriptive Feature Transformation",
        "raw_input": str(raw_path.relative_to(ROOT)).replace("\\", "/"),
        "processed_output": str(PROCESSED_OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "feature_matrix": str(FEATURE_MATRIX_OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "records": len(processed_rows),
        "categories": category_map,
        "subcategories": subcategory_map,
        "descriptive_features": DESCRIPTIVE_FEATURES,
        "raw_immutable": True,
    }
    save_json(MANIFEST_OUTPUT, manifest)
    manifest["validation"] = validate(raw_path, PROCESSED_OUTPUT, FEATURE_MATRIX_OUTPUT)
    return manifest


# Alias tương thích ngược
run = run_preprocessing


# -----------------------------------------------------------------------------
# 3. TỔ CHỨC CHUYÊN MỤC & TRÍCH XUẤT TỪ KHÓA XU HƯỚNG
# -----------------------------------------------------------------------------

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


def run_organization(source_path: Path | None = None) -> dict[str, Any]:
    """Thực thi tự động tổ chức danh mục và lưu tệp JSON tổng hợp."""
    src = source_path or (PROCESSED_OUTPUT if PROCESSED_OUTPUT.exists() else RAW)
    if not src.exists():
        raise FileNotFoundError(f"Input dataset not found at {src}")
    records = load_jsonl(src)
    summary = compute_category_summary(records)
    save_json(SUMMARY_PATH, summary)
    return summary


# -----------------------------------------------------------------------------
# 4. ENTRYPOINT DÒNG LỆNH CHUNG CHO PHASE TRANSFORM
# -----------------------------------------------------------------------------

def main() -> None:
    """Entrypoint dòng lệnh cho Phase T — Transform (Tiền xử lý & Tổ chức chuyên mục)."""
    parser = argparse.ArgumentParser(description="Pipeline tiền xử lý dữ liệu và trích xuất đặc trưng mô tả")
    parser.add_argument("--check", "--validate-only", action="store_true", help="Chỉ kiểm định tính toàn vẹn dữ liệu đã tiền xử lý")
    args = parser.parse_args()

    if args.check:
        val_p = validate()
        val_s = validate_summary()
        res = {"preprocessing": val_p, "category_summary": val_s}
        print(json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(0 if (val_p.get("result") == "PASS" and val_s.get("result") == "PASS") else 1)

    manifest = run_preprocessing()
    val_p = manifest.get("validation", {})
    status_p = val_p.get("result", "UNKNOWN")
    print(f"Tiền xử lý hoàn tất: {status_p} ({manifest.get('records', 0)} bản ghi, {len(DESCRIPTIVE_FEATURES)} đặc trưng mô tả)")

    summary = run_organization()
    val_s = validate_summary()
    status_s = val_s.get("result", "PASS")
    print(f"Tổ chức danh mục hoàn tất: {status_s} ({summary.get('total_articles', 0)} bài, {summary.get('total_categories', 0)} chuyên mục)")

    sys.exit(0 if (status_p == "PASS" and status_s == "PASS") else 1)


if __name__ == "__main__":
    main()
