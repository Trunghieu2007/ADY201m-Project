from __future__ import annotations

import csv
import json
import logging
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger(__name__)

# Paths & Constants
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "articles.jsonl"
OUT = ROOT / "data" / "processed"
REPORTS = ROOT / "outputs" / "preprocessing"
PROCESSED_OUTPUT = OUT / "articles_processed.jsonl"
FEATURE_MATRIX_OUTPUT = OUT / "feature_matrix.csv"
MANIFEST_OUTPUT = REPORTS / "phase3_manifest.json"

_WHITESPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)

DESCRIPTIVE_FEATURES = [
    "char_count", "word_count", "sentence_count", "unique_word_count",
    "lexical_diversity", "avg_word_length", "title_char_count", "title_word_count",
    "description_char_count", "description_word_count", "title_to_content_word_ratio",
    "publication_hour", "publication_weekday",
]
CORE_RAW_FIELDS = (
    "url", "title", "description", "content", "author", "publisher",
    "published_at", "category", "subcategory", "article_id", "crawled_at", "source",
)


# 1. Text & Author Cleaning
def normalize_unicode(text: str | None) -> str:
    """Chuẩn hóa văn bản tiếng Việt sang dạng Unicode chuẩn NFC."""
    return unicodedata.normalize("NFC", str(text)) if text else ""


def normalize_text(text: str | None) -> str:
    """Loại bỏ URL rác, chuẩn hóa khoảng trắng thừa và ký tự không ngắt \u00a0."""
    cleaned = _URL_RE.sub(" ", normalize_unicode(text)).replace("\u00a0", " ")
    return _WHITESPACE_RE.sub(" ", cleaned).strip()


def tokenize(text: str | None) -> list[str]:
    """Tách từ cơ bản dựa trên khoảng trắng."""
    return normalize_text(text).split() if text else []


def sentence_count(text: str | None) -> int:
    """Đếm số câu dựa trên các dấu kết thúc câu (.!?…)."""
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


# 2. Preprocessing & Feature Extraction
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


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


# 3. Self-Validation (No SHA-256)
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


# 4. Pipeline Runner
def run(raw_path: Path = RAW) -> dict:
    """Điều phối toàn bộ quy trình Transform: làm sạch, trích xuất đặc trưng và tự kiểm định."""
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    raw_rows = load_jsonl(raw_path)

    categories = sorted({r["category"] for r in raw_rows if r.get("category")})
    subcategories = sorted({r["subcategory"] for r in raw_rows if r.get("subcategory")})
    category_map = {v: i + 1 for i, v in enumerate(categories)}
    subcategory_map = {v: i + 1 for i, v in enumerate(subcategories)}

    processed_rows = [preprocess_record(r, category_map, subcategory_map) for r in raw_rows]

    with PROCESSED_OUTPUT.open("w", encoding="utf-8") as f:
        for r in processed_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

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
    MANIFEST_OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest["validation"] = validate(raw_path, PROCESSED_OUTPUT, FEATURE_MATRIX_OUTPUT)
    return manifest


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    res = run()
    print(json.dumps(res, ensure_ascii=False, indent=2))
