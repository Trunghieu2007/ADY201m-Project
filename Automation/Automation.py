import os
import subprocess
import sys
import time
from datetime import datetime

# Đảm bảo in tiếng Việt không bị lỗi trên Windows
sys.stdout.reconfigure(encoding="utf-8")

# Thư mục gốc của toàn dự án (thư mục cha của thư mục Automation)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(BASE_DIR, "scheduler.log")

# Năm bước của chuỗi pipeline xử lý dữ liệu và AI (luôn chạy đúng thứ tự này)
STEPS = [
    ("Step 1: Raw Crawler", os.path.join(BASE_DIR, "Phase 1 - Data crawl & Post process + Quick report", "Step1_RawCrawler.py")),
    ("Step 2: Data Filter", os.path.join(BASE_DIR, "Phase 1 - Data crawl & Post process + Quick report", "Step2_DataFilter.py")),
    ("Step 3: Train model", os.path.join(BASE_DIR, "Train model", "TrainClassifier.py")),
    ("Step 4: SQL importer", os.path.join(BASE_DIR, "Phase 2 - Import data to SQL", "SQLimporter.py")),
    ("Step 5: EDA + charts", os.path.join(BASE_DIR, "Phase 3 - EDA", "Charts.py")),
]

# Ghi một dòng thông điệp kèm timestamp hiện tại vào tệp nhật ký scheduler.log
def ghi_log(noi_dung):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {noi_dung}\n")

# Chạy một script con bằng đúng Python đang dùng, dừng chuỗi nếu thất bại
def chay_buoc(ten, duong_dan):
    print(f"\n[{datetime.now():%d/%m/%Y %H:%M:%S}] Bắt đầu {ten}")
    ket_qua = subprocess.run([sys.executable, duong_dan], cwd=BASE_DIR)
    if ket_qua.returncode != 0:
        print(f"[!] {ten} thất bại (mã {ket_qua.returncode}), dừng chuỗi lần này.")
        ghi_log(f"{ten} thất bại (mã {ket_qua.returncode})")
        return False
    return True

# Chạy lần lượt 5 bước của pipeline, dừng ngay khi một bước gặp lỗi
def chay_chuoi():
    ghi_log("Bắt đầu chuỗi 5 bước")
    for ten, duong_dan in STEPS:
        if not chay_buoc(ten, duong_dan):
            return False
    ghi_log("Hoàn tất chuỗi 5 bước")
    return True

# Điều phối chạy trọn vẹn một lần chuỗi 5 bước pipeline của dự án
def main():
    print("Bắt đầu chạy chuỗi 5 bước (Raw Crawl -> Filter -> AI Classifier -> SQL -> EDA)...")
    thanh_cong = chay_chuoi()
    if thanh_cong:
        print("\n[+] Đã hoàn thành xuất sắc toàn bộ chuỗi 5 bước của hệ thống!")
    else:
        print("\n[!] Chuỗi pipeline đã dừng do có bước gặp lỗi.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nĐã dừng automation.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nĐã dừng automation.")
