"""Module kiểm định tính toàn vẹn và hợp lệ của dữ liệu sau tiền xử lý (Phase T - Transform)."""
from __future__ import annotations

import json
from pathlib import Path
from .preprocess import RAW, PROCESSED_OUTPUT, FEATURE_MATRIX_OUTPUT, validate as run_validation


def validate(
    raw_path: Path = RAW,
    processed_path: Path = PROCESSED_OUTPUT,
    feature_path: Path = FEATURE_MATRIX_OUTPUT,
) -> dict:
    """Kiểm tra tính bất biến của dữ liệu gốc và tính hợp lệ của dữ liệu tiền xử lý."""
    return run_validation(raw_path, processed_path, feature_path)


if __name__ == "__main__":
    res = validate()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    raise SystemExit(0 if res["result"] == "PASS" else 1)
