# Tiện ích khởi chạy ứng dụng Streamlit BI Dashboard cho ADY201m
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# Khởi chạy quy trình Streamlit run app.py
def main() -> int:
    app = Path(__file__).resolve().parent / "app.py"
    return subprocess.call([sys.executable, "-m", "streamlit", "run", str(app)])


if __name__ == "__main__":
    raise SystemExit(main())
