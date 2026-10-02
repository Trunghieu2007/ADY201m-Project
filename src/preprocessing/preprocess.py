from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from .author_cleaning import normalize_author
from .text_cleaning import lexical_features, normalize_text, remove_leading_duplicate_blocks, tokenize

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "articles.jsonl"
OUT = ROOT / "data" / "processed"
REPORTS = ROOT / "outputs" / "preprocessing"


# Đọc file dữ liệu JSONL thành danh sách dictionary
def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# Tính mã băm SHA-256 của file để xác thực tính toàn vẹn
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# Phân tích chuỗi ISO datetime sang datetime object
def parse_dt(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


# Tiền xử lý văn bản, trích xuất đặc trưng và chuẩn hóa metadata cho một bài viết
def preprocess_record(record: dict, category_map: dict[str, int], subcategory_map: dict[str, int]) -> dict:
    title = normalize_text(record.get("title"))
    description = normalize_text(record.get("description"))
    content_raw = normalize_text(record.get("content"))
    content = remove_leading_duplicate_blocks(content_raw, title, description)
    combined = " ".join(x for x in (title, description, content) if x)
    content_features = lexical_features(content)
    title_features = lexical_features(title)
    description_features = lexical_features(description)
    dt = parse_dt(record.get("published_at"))

    features = {
        **content_features,
        "title_char_count": title_features["char_count"],
        "title_word_count": title_features["word_count"],
        "description_char_count": description_features["char_count"],
        "description_word_count": description_features["word_count"],
        "title_to_content_word_ratio": round(title_features["word_count"] / content_features["word_count"], 6) if content_features["word_count"] else 0.0,
        "category_id": category_map[record["category"]],
        "subcategory_id": subcategory_map.get(record.get("subcategory"), 0),
        "publication_hour": dt.hour if dt else -1,
        "publication_weekday": dt.weekday() if dt else -1,
    }

    return {
        **record,
        "processed_text": {
            "title_clean": title,
            "description_clean": description,
            "content_clean": content,
            "content_cleaning": {
                "raw_char_count": len(content_raw),
                "clean_char_count": len(content),
                "leading_duplicate_removed": len(content) < len(content_raw),
            },
            "combined_text": combined,
            "content_tokens": tokenize(content),
        },
        "processed_metadata": {
            "author_clean": normalize_author(record.get("author")),
            "category_id": features["category_id"],
            "subcategory_id": features["subcategory_id"],
        },
        "features": features,
    }


# Xây dựng ma trận đặc trưng số học và one-hot encoding từ danh sách bài viết
def build_feature_matrix(rows: list[dict]) -> tuple[list[str], list[list[float | int]]]:
    numeric = [
        "char_count", "word_count", "sentence_count", "unique_word_count",
        "lexical_diversity", "avg_word_length", "title_char_count", "title_word_count",
        "description_char_count", "description_word_count", "title_to_content_word_ratio",
        "publication_hour", "publication_weekday", "category_id", "subcategory_id",
    ]
    categories = sorted({r["category"] for r in rows})
    subcategories = sorted({r["subcategory"] for r in rows if r.get("subcategory")})
    header = ["article_id", *numeric, *(f"category__{x}" for x in categories), *(f"subcategory__{x}" for x in subcategories)]
    matrix = []
    for r in rows:
        f = r["features"]
        values = [f[k] for k in numeric]
        values += [1 if r["category"] == c else 0 for c in categories]
        values += [1 if r.get("subcategory") == s else 0 for s in subcategories]
        matrix.append([r["article_id"], *values])
    return header, matrix


# Ghi dữ liệu dạng bảng ra file CSV UTF-8
def write_csv(path: Path, header: list[str], rows: list[list]):
    import csv
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


# Điều phối toàn bộ quy trình tiền xử lý Phase 3 và xuất file artifacts
def run() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    raw_hash, raw_rows = sha256(RAW), load_jsonl(RAW)
    categories = sorted({r["category"] for r in raw_rows})
    subcategories = sorted({r["subcategory"] for r in raw_rows if r.get("subcategory")})
    category_map = {v: i + 1 for i, v in enumerate(categories)}
    subcategory_map = {v: i + 1 for i, v in enumerate(subcategories)}
    rows = [preprocess_record(r, category_map, subcategory_map) for r in raw_rows]

    processed = OUT / "articles_processed.jsonl"
    with processed.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    header, matrix = build_feature_matrix(rows)
    write_csv(OUT / "feature_matrix.csv", header, matrix)

    manifest = {
        "phase": "Phase 3 — Data Preprocessing & Feature Engineering",
        "version": "1.0", "raw_input": "data/raw/articles.jsonl", "raw_sha256": raw_hash,
        "processed_output": "data/processed/articles_processed.jsonl",
        "feature_matrix": "data/processed/feature_matrix.csv",
        "records": len(rows), "categories": category_map, "subcategories": subcategory_map,
        "transformations": [
            "Unicode NFC normalization",
            "conservative removal of exact leading title/description duplication",
            "whitespace normalization", "URL removal from derived text only",
            "conservative author normalization in author_clean",
            "deterministic lexical/text features",
            "integer encoding for category and subcategory",
            "one-hot encoding for category and subcategory in feature_matrix.csv",
        ],
        "raw_immutable": True,
    }
    (REPORTS / "phase3_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    feature_summary = {
        "records": len(rows), "feature_count": len(header) - 1, "feature_columns": header[1:],
        "processed_sha256": sha256(processed), "feature_matrix_sha256": sha256(OUT / "feature_matrix.csv"),
    }
    (REPORTS / "feature_summary.json").write_text(json.dumps(feature_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
