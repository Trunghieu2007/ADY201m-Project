from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/articles.jsonl"
PROCESSED = ROOT / "data/processed/articles_processed.jsonl"
FEATURES = ROOT / "data/processed/feature_matrix.csv"
MANIFEST = ROOT / "outputs/preprocessing/phase3_manifest.json"


# Tính chuỗi băm SHA-256 của file được chỉ định
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# Đọc file dữ liệu JSONL thành danh sách object
def load(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


# Kiểm tra tính toàn vẹn và không phá hủy dữ liệu gốc của Phase 3
def validate() -> dict:
    raw_hash_before = sha256(RAW)
    raw = load(RAW)
    processed = load(PROCESSED)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors = []
    if len(raw) != len(processed):
        errors.append("record_count_mismatch")
    if raw_hash_before != manifest["raw_sha256"]:
        errors.append("raw_hash_manifest_mismatch")
    if [r["article_id"] for r in raw] != [r["article_id"] for r in processed]:
        errors.append("article_order_or_ids_changed")
    for i, (r, p) in enumerate(zip(raw, processed), 1):
        for k in ("url", "title", "description", "content", "author", "published_at", "category", "subcategory", "article_id", "crawled_at", "source"):
            if p.get(k) != r.get(k):
                errors.append(f"raw_field_changed_record_{i}:{k}")
        if not p.get("processed_text", {}).get("content_clean", "") and r.get("content"):
            errors.append(f"empty_processed_content_record_{i}")
        if "features" not in p:
            errors.append(f"missing_features_record_{i}")
    header = FEATURES.read_text(encoding="utf-8").splitlines()[0].split(",")
    if len(header) < 10:
        errors.append("feature_matrix_too_small")
    return {"result": "PASS" if not errors else "FAIL", "errors": errors, "records": len(processed), "feature_columns": len(header) - 1}


if __name__ == "__main__":
    res = validate()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    raise SystemExit(0 if res["result"] == "PASS" else 1)
