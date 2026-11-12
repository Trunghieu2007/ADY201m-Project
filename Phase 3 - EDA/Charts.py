import os
import sys
import json
import calendar
# pyrefly: ignore[missing-import]
import pyodbc  # type: ignore
# pyrefly: ignore[missing-import]
import pandas as pd  # type: ignore
# pyrefly: ignore[missing-import]
import matplotlib.pyplot as plt  # type: ignore

# Đảm bảo hiển thị tiếng Việt chuẩn trên Console và Biểu đồ
sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# Thư mục lưu file biểu đồ đầu ra (cùng thư mục với script này)
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SAVE_DIR)

# Bảng 20 màu rời cách đều: thấp nhất = xanh biển -> giữa = xanh lá -> cao nhất = đỏ
PALETTE = [
    "#1f78b4", "#2685a8", "#2d939c", "#319b8a", "#33a277",
    "#31a35d", "#2ea140", "#41a833", "#5fb230", "#7ebb2e",
    "#9dc32e", "#b7c72d", "#c8c52c", "#d8be29", "#e3ae25",
    "#ec9c21", "#eb801f", "#eb641d", "#e73f1c", "#e31a1c"
]

# Tải dữ liệu từ SQL Server, tự động fallback đọc file JSON nếu SQL chưa sẵn sàng
def get_data():
    conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\\SQLEXPRESS;DATABASE=ADY201m;Trusted_Connection=yes;"
    try:
        conn = pyodbc.connect(conn_str, timeout=3)
        cur = conn.cursor()
        cur.execute(
            "SELECT article_id, title, description, content, author, published_at, "
            "category, subcategory FROM dbo.VnExpress_Articles"
        )
        df = pd.DataFrame.from_records(cur.fetchall(), columns=[c[0] for c in cur.description])
        cur.close()
        conn.close()
        if not df.empty:
            print(f"[*] Đã tải thành công {len(df)} bài báo từ SQL Server (ADY201m).")
            return df
    except Exception as e:
        print(f"[!] Không thể kết nối SQL Server ({e}). Chuyển sang nạp file JSON dự phòng...")

    # Fallback: đọc trực tiếp file JSON từ Phase 1
    json_path = os.path.join(PROJECT_DIR, "Phase 1 - Data crawl & Post process + Quick report", "vnexpress_data.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        rel_path = os.path.relpath(json_path, PROJECT_DIR)
        print(f"[*] Nạp thành công {len(df)} bài viết từ file JSON dự phòng: {rel_path}")
        return df

    return pd.DataFrame()

# Gán mỗi giá trị vào 1 trong 20 bậc màu rời cách đều trên đoạn [min, max]
def mau_theo_gia_tri(values):
    vmin, vmax = min(values), max(values)
    if vmax == vmin:
        return [PALETTE[len(PALETTE) // 2]] * len(values)
    return [PALETTE[int(round((v - vmin) / (vmax - vmin) * (len(PALETTE) - 1)))] for v in values]

# Lưu figure ra tệp PNG với độ phân giải cao và giải phóng bộ nhớ
def luu_anh(fig, ten_file, rect=(0, 0, 1, 1)):
    fig.tight_layout(rect=rect)
    fig.savefig(os.path.join(SAVE_DIR, ten_file), dpi=200, facecolor="white")
    plt.close(fig)
    print(f"[+] Đã lưu: {ten_file}")

# Biểu đồ 1: Số bài theo chuyên mục (cột ngang, tô màu theo số lượng)
def ve_bieu_do_1(df):
    cat = df["category"].fillna("Khác").str.strip().value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(cat.index, cat.values, edgecolor="black", color=mau_theo_gia_tri(list(cat.values)))
    for b, v in zip(bars, cat.values):
        pct = f"{v / len(df) * 100:.1f}".replace(".", ",")
        ax.text(v + 0.15, b.get_y() + b.get_height() / 2, f"{v}  ({pct}%)", va="center", fontsize=9)
    ax.set_title(f"Số bài theo chuyên mục (n={len(df)})", fontsize=13, fontweight="bold")
    ax.set_xlabel("Số lượng bài viết")
    ax.set_xlim(0, cat.max() * 1.18)
    ax.grid(axis="x", linestyle=":", alpha=0.45)
    ax.set_axisbelow(True)
    luu_anh(fig, "bieu_do_1_chuyen_muc.png")

# Biểu đồ 2: Tần số bài xuất bản theo 24 khung giờ trong ngày
def ve_bieu_do_2(df):
    hour = df["hour"].dropna().astype(int)
    dem = hour.value_counts().reindex(range(24), fill_value=0)
    fig, ax = plt.subplots(figsize=(13, 6.5))
    bars = ax.bar(dem.index, dem.values, width=0.82, edgecolor="black", color=mau_theo_gia_tri(list(dem.values)))
    for b, v in zip(bars, dem.values):
        if v:
            ax.text(b.get_x() + b.get_width() / 2, v + 0.2, int(v), ha="center", va="bottom", fontsize=9)
    ax.set_title(f"Số bài xuất bản theo khung giờ (n={len(hour)})", fontsize=13, fontweight="bold")
    ax.set_xlabel("Khung giờ trong ngày")
    ax.set_ylabel("Số bài viết")
    ax.set_xticks(range(24), [f"{h}h" for h in range(24)])
    ax.tick_params(axis="x", labelsize=8)
    ax.set_xlim(-0.6, 23.6)
    ax.set_ylim(0, dem.max() * 1.18)
    ax.grid(axis="y", linestyle=":", alpha=0.45)
    ax.set_axisbelow(True)
    luu_anh(fig, "bieu_do_2_phan_bo_gio.png")

# Biểu đồ 3: Cơ cấu tác giả bài viết (tròn: VnExpress vs Khác)
def ve_bieu_do_3(df):
    author = df["author"].fillna("VnExpress").str.strip()
    vne = int((author == "VnExpress").sum())
    vals = [vne, len(author) - vne]
    labels = ["VnExpress", "Các tác giả khác"]
    colors = ["#1f78b4", "#bdbdbd"]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.pie(
        vals, labels=labels, colors=colors, startangle=90, counterclock=False, pctdistance=0.7,
        autopct=lambda p: f"{p:.1f}%".replace(".", ","),
        wedgeprops={"edgecolor": "white", "linewidth": 1.5}, textprops={"fontsize": 10}
    )
    ax.set_title(f"Cơ cấu tác giả bài viết (n={len(df)})", fontsize=13, fontweight="bold")
    luu_anh(fig, "bieu_do_3_tac_gia.png")

# Biểu đồ 4: Bản đồ nhiệt 1 tháng dạng ma trận Lịch (Calendar Heatmap không trục)
def ve_bieu_do_4(df):
    valid_dates = df["published_at"].dropna()
    if valid_dates.empty:
        return

    latest = valid_dates.max()
    year, month = latest.year, latest.month
    month_data = df[(df["published_at"].dt.year == year) & (df["published_at"].dt.month == month)]
    day_counts = month_data["published_at"].dt.day.value_counts().to_dict()

    cal = calendar.monthcalendar(year, month)
    vmax = max(day_counts.values()) if day_counts else 1

    fig, ax = plt.subplots(figsize=(10, 7.5))

    # Nhãn các thứ trong tuần ở trên đỉnh mỗi cột (T2 đến CN)
    weekday_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
    for c, wname in enumerate(weekday_names):
        ax.text(c + 0.5, len(cal) + 0.25, wname, ha="center", va="center",
                fontsize=11, fontweight="bold", color="#333333")

    for r, week in enumerate(cal):
        for c, day in enumerate(week):
            y_pos = len(cal) - 1 - r
            if day == 0:
                color = "#f4f4f4"
                rect = plt.Rectangle((c, y_pos), 1, 1, facecolor=color, edgecolor="white", linewidth=2.5)
                ax.add_patch(rect)
            else:
                val = day_counts.get(day, 0)
                if val == 0:
                    color = "#e8e8e8"
                    txt_color = "#888888"
                else:
                    color_idx = int(round((val / vmax) * (len(PALETTE) - 1)))
                    color = PALETTE[min(len(PALETTE) - 1, color_idx)]
                    txt_color = "white"

                rect = plt.Rectangle((c, y_pos), 1, 1, facecolor=color, edgecolor="white", linewidth=2.5)
                ax.add_patch(rect)

                txt = f"{day}\n({val})" if val > 0 else f"{day}"
                ax.text(c + 0.5, y_pos + 0.5, txt, ha="center", va="center",
                        fontsize=11, fontweight="bold", color=txt_color)

    ax.set_xlim(0, 7)
    ax.set_ylim(-0.2, len(cal) + 0.6)
    ax.axis("off")  # Tuyệt đối không hiển thị đường trục tọa độ
    ax.set_title(f"Bản đồ nhiệt mật độ bài viết tháng {month}/{year} (n={len(month_data)})",
                 fontsize=14, fontweight="bold", pad=15)

    luu_anh(fig, "bieu_do_4_nhiet_do_thang.png", rect=[0.05, 0.05, 0.95, 0.95])

# Quy trình EDA: nạp dữ liệu, tính thống kê mô tả và xuất 4 biểu đồ PNG
def generate_eda_charts():
    df = get_data()
    if df.empty:
        print("[!] Không có dữ liệu, dừng xuất biểu đồ.")
        return

    # Tiền xử lý các trường phục vụ phân tích
    df["content"] = df["content"].fillna("")
    df["description"] = df["description"].fillna("")
    df["word_count"] = df["content"].str.split().str.len()
    df["desc_wc"] = df["description"].str.split().str.len()
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    df["hour"] = df["published_at"].dt.hour

    # In thông tin tổng quan tinh gọn
    print(f"[+] Tổng số bài viết: {len(df)}")
    print(f"[+] Độ dài trung bình: {df['word_count'].mean():.1f} từ (Ngắn nhất: {df['word_count'].min()}, Dài nhất: {df['word_count'].max()})")
    print(f"[+] Số chuyên mục: {df['category'].nunique()} chuyên mục")

    # Xuất 4 biểu đồ
    ve_bieu_do_1(df)
    ve_bieu_do_2(df)
    ve_bieu_do_3(df)
    ve_bieu_do_4(df)

    print("[+] Hoàn tất! Đã xuất 4 biểu đồ ra 4 file PNG riêng biệt.")

if __name__ == "__main__":
    generate_eda_charts()
