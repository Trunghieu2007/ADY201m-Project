import os
import subprocess
import sys
import time
from datetime import datetime

# Đảm bảo in tiếng Việt không bị lỗi trên Windows
sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "scheduler.log")
INTERVAL = 30 * 60  # 30 phút, tính từ lúc bắt đầu mỗi lần chạy

# Ba bước của chuỗi, luôn chạy đúng thứ tự này
STEPS = [
    ("Web crawler", os.path.join(BASE_DIR, "Web crawler", "Webcrawler.py")),
    ("SQL importer", os.path.join(BASE_DIR, "SQL importer", "SQLimporter.py")),
    ("EDA + charts", os.path.join(BASE_DIR, "EDA + charts", "Charts.py")),
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

#chay_chuoi: chạy lần lượt 3 bước, dừng ngay khi một bước lỗi
def chay_chuoi():
    ghi_log("Bắt đầu chuỗi 3 bước")
    for ten, duong_dan in STEPS:
        if not chay_buoc(ten, duong_dan):
            return False
    ghi_log("Hoàn tất chuỗi 3 bước")
    return True

#main: chạy ngay một lần, sau đó lặp lại mỗi 30 phút cho tới khi nhấn Ctrl+C
def main():
    print(f"Chuỗi 3 bước sẽ chạy mỗi {INTERVAL // 60} phút. Nhấn Ctrl+C để dừng.")
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
        print("\nĐã dừng scheduler.")
