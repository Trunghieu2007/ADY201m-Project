"""Script thực thi và kiểm định toàn bộ pipeline tiền xử lý dữ liệu (Phase T - Transform)."""
from __future__ import annotations

import sys
from .preprocess import run, validate

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if __name__ == "__main__":
    manifest = run()
    res = validate()
    print(f"Tiền xử lý hoàn tất: {res['result']} ({res['records']} bản ghi, {res['features_count']} đặc trưng mô tả)")
    raise SystemExit(0 if res["result"] == "PASS" else 1)
