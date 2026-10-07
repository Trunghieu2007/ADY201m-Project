"""Trình điều phối đường ống dữ liệu hợp nhất (Unified Pipeline Runner) cho ADY201m.
Cung cấp giao diện dòng lệnh (CLI) 1-Click để thực thi toàn bộ hoặc từng phân hệ:
Crawler -> Validation -> EDA -> Preprocessing -> Taxonomy -> Audit -> Dashboard.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from src.utils import PROJECT_ROOT


def run_stage_validate_raw() -> bool:
    """Chặng 1: Kiểm định tính hợp lệ của dữ liệu thô."""
    print("\n" + "=" * 60)
    print("🚀 [CHẶNG 1/5] KIỂM ĐỊNH KỸ THUẬT DỮ LIỆU THÔ (RAW DATA VALIDATION)")
    print("=" * 60)
    from src.validation.validate_raw import main as validate_main
    return validate_main() == 0


def run_stage_eda() -> bool:
    """Chặng 2: Khám phá dữ liệu (EDA) và xuất 6 biểu đồ trực quan hóa."""
    print("\n" + "=" * 60)
    print("📊 [CHẶNG 2/5] KHÁM PHÁ DỮ LIỆU (EDA) & XUẤT 6 BIỂU ĐỒ TRỰC QUAN")
    print("=" * 60)
    from src.eda.run_eda import main as eda_main
    return eda_main() == 0


def run_stage_preprocess() -> bool:
    """Chặng 3: Tiền xử lý, chuẩn hóa Unicode NFC và trích xuất 13 đặc trưng."""
    print("\n" + "=" * 60)
    print("⚙️ [CHẶNG 3/5] TIỀN XỬ LÝ (PREPROCESSING) & TRÍCH XUẤT 13 ĐẶC TRƯNG")
    print("=" * 60)
    from src.preprocessing.preprocess import run as preprocess_run
    manifest = preprocess_run()
    val = manifest.get("validation", {})
    return val.get("result") == "PASS"


def run_stage_organize() -> bool:
    """Chặng 4: Tự động tổ chức chuyên mục và trích xuất từ khóa xu hướng."""
    print("\n" + "=" * 60)
    print("📑 [CHẶNG 4/5] TỔ CHỨC CHUYÊN MỤC & TOP TỪ KHÓA XU HƯỚNG")
    print("=" * 60)
    from src.organization.category_organizer import run_organization, validate_summary
    run_organization()
    val = validate_summary()
    return val.get("result") == "PASS"


def run_stage_audit() -> bool:
    """Chặng 5: Kiểm toán toàn diện chất lượng và tính toàn vẹn hệ thống."""
    print("\n" + "=" * 60)
    print("🛡️ [CHẶNG 5/5] KIỂM TOÁN TOÀN DIỆN HỆ THỐNG (PROJECT AUDIT)")
    print("=" * 60)
    from src.validation.project_audit import main as audit_main
    res = audit_main()
    status = res.get("audit", {}).get("status")
    print(f"Trạng thái kiểm toán: {status}")
    return status in {"PASS", "PASS_WITH_REVIEW"}


def run_tests() -> bool:
    """Chạy toàn bộ bộ kiểm thử hồi quy tự động (unittest)."""
    print("\n" + "=" * 60)
    print("🧪 CHẠY BỘ KIỂM THỬ HỒI QUY TỰ ĐỘNG (UNIT TESTS)")
    print("=" * 60)
    ret = subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    return ret == 0


def run_dashboard() -> None:
    """Khởi chạy ứng dụng BI Dashboard Streamlit."""
    print("\n" + "=" * 60)
    print("📰 KHỞI CHẠY GIAO DIỆN BI DASHBOARD STREAMLIT...")
    print("=" * 60)
    app_path = PROJECT_ROOT / "dashboard" / "app.py"
    subprocess.call([sys.executable, "-m", "streamlit", "run", str(app_path)])


def main() -> None:
    """Điểm khởi chạy chính CLI."""
    parser = argparse.ArgumentParser(
        description="Trình điều phối đường ống dữ liệu ADY201m (Unified Data Pipeline Runner)"
    )
    parser.add_argument(
        "--stage",
        choices=["crawl", "validate", "eda", "preprocess", "organize", "db", "audit", "all"],
        default="all",
        help="Chọn chặng xử lý muốn chạy (mặc định: 'all')",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Khởi chạy ngay giao diện Streamlit Dashboard",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Chạy toàn bộ bộ kiểm thử tự động unittest",
    )
    args = parser.parse_args()

    if args.dashboard:
        run_dashboard()
        return

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    start_time = time.time()

    if args.stage == "crawl":
        from src.crawler.crawler import main as crawl_main
        crawl_main()
        return

    if args.stage == "validate":
        ok = run_stage_validate_raw()
        sys.exit(0 if ok else 1)

    if args.stage == "eda":
        ok = run_stage_eda()
        sys.exit(0 if ok else 1)

    if args.stage == "preprocess":
        ok = run_stage_preprocess()
        sys.exit(0 if ok else 1)

    if args.stage == "organize":
        ok = run_stage_organize()
        sys.exit(0 if ok else 1)

    if args.stage == "db":
        from src.database.sqlserver import main as db_main
        db_main()
        return

    if args.stage == "audit":
        ok = run_stage_audit()
        sys.exit(0 if ok else 1)

    # Chạy toàn bộ quy trình tuần tự khép kín (End-to-End Pipeline)
    print("=" * 70)
    print("🌟 BẮT ĐẦU CHẠY TOÀN BỘ ĐƯỜNG ỐNG DỮ LIỆU ADY201M (END-TO-END PIPELINE)")
    print("=" * 70)

    stages = [
        ("Kiểm định thô", run_stage_validate_raw),
        ("Khám phá EDA", run_stage_eda),
        ("Tiền xử lý", run_stage_preprocess),
        ("Tổ chức chuyên mục", run_stage_organize),
        ("Kiểm toán toàn diện", run_stage_audit),
    ]

    for name, func in stages:
        if not func():
            print(f"\n❌ [THẤT BẠI] Chặng '{name}' gặp sự cố. Dừng tiến trình!")
            sys.exit(1)

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"🎉 HOÀN TẤT TOÀN BỘ PIPELINE THÀNH CÔNG RỰC RỠ! (Thời gian: {elapsed:.2f}s)")
    print("💡 Mở Dashboard để xem trực quan hóa: python run_pipeline.py --dashboard")
    print("=" * 70)


if __name__ == "__main__":
    main()
