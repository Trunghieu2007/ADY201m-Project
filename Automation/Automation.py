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
INTERVAL = 30 * 60  # 30 phút, tính từ lúc bắt đầu mỗi lần chạy

# Năm bước của chuỗi pipeline xử lý dữ liệu và AI (luôn chạy đúng thứ tự này)
STEPS = [
    ("Step 1: Raw Crawler", os.path.join(BASE_DIR, "Phase 1 - Data crawl & Post process + Quick report", "Step1_RawCrawler.py")),
    ("Step 2: Data Filter", os.path.join(BASE_DIR, "Phase 1 - Data crawl & Post process + Quick report", "Step2_DataFilter.py")),
    ("Step 3: Train model", os.path.join(BASE_DIR, "Train model", "TrainClassifier.py")),
    ("Step 4: SQL importer", os.path.join(BASE_DIR, "Phase 2 - Import data to SQL", "SQLimporter.py")),
    ("Step 5: EDA + charts", os.path.join(BASE_DIR, "Phase 3 - EDA", "Charts.py")),
]

#ghi_log: thêm một dòng có thời gian vào scheduler.log để xem lại các lần chạy
def ghi_log(noi_dung):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {noi_dung}\n")

#chay_buoc: chạy một script con bằng đúng Python đang dùng, trả về True nếu thành công
def chay_buoc(ten, duong_dan):
    print(f"\n[{datetime.now():%d/%m/%Y %H:%M:%S}] Bắt đầu {ten}")
    ket_qua = subprocess.run([sys.executable, duong_dan], cwd=BASE_DIR)
    if ket_qua.returncode != 0:
        print(f"[!] {ten} thất bại (mã {ket_qua.returncode}), dừng chuỗi lần này.")
        ghi_log(f"{ten} thất bại (mã {ket_qua.returncode})")
        return False
    return True

#chay_chuoi: chạy lần lượt 4 bước, dừng ngay khi một bước lỗi
def chay_chuoi():
    ghi_log("Bắt đầu chuỗi 5 bước")
    for ten, duong_dan in STEPS:
        if not chay_buoc(ten, duong_dan):
            return False
    ghi_log("Hoàn tất chuỗi 5 bước")
    return True

#main: chạy ngay một lần, sau đó lặp lại mỗi 30 phút cho tới khi nhấn Ctrl+C
def main():
    print(f"Chuỗi 5 bước (Raw Crawl -> Filter -> AI Classifier -> SQL -> EDA) sẽ chạy mỗi {INTERVAL // 60} phút. Nhấn Ctrl+C để dừng.")
    while True:
        bat_dau = time.time()
        chay_chuoi()
        cho = INTERVAL - (time.time() - bat_dau)
        if cho > 0:
            print(f"\nLần chạy kế tiếp sau {cho / 60:.1f} phút.")
            time.sleep(cho)
        else:
            print(f"\nChuỗi chạy lâu hơn {INTERVAL // 60} phút, bắt đầu lần kế tiếp ngay.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nĐã dừng automation.")
