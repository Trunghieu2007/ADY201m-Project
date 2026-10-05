"""Script khởi chạy đồng bộ và kiểm định CSDL Microsoft SQL Server 3NF (Phase L - Load)."""
from __future__ import annotations

import sys
from .sqlserver import main

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if __name__ == "__main__":
    raise SystemExit(main())
