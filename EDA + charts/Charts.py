import os
import sys
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

#Truy vấn dữ liệu bài báo từ SQL Server và trả về pandas DataFrame
def get_data_from_sql():
    conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\\SQLEXPRESS;DATABASE=ADY201m;Trusted_Connection=yes;"
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT article_id, title, content, author, published_at, category FROM dbo.VnExpress_Articles")
    cols = [c[0] for c in cur.description]
    df = pd.DataFrame.from_records(cur.fetchall(), columns=cols)
    cur.close()
    conn.close()
    return df

#Bộ thống kê mô tả gọn: bỏ phân vị (25/50/75), đổi nhãn viết tắt sang tên đầy đủ
def thong_ke(series):
    s = series.dropna()
    return pd.Series({
        "Số bài (count)": len(s),
        "Trung bình (mean)": round(float(s.mean()), 2),
        "Độ lệch chuẩn (std)": round(float(s.std()), 2),
        "Giá trị nhỏ nhất (min)": int(s.min()),
        "Giá trị lớn nhất (max)": int(s.max()),
    })

#Lưu một figure ra PNG riêng rồi đóng lại
def luu_anh(fig, ten_file):
    fig.tight_layout()
    fig.savefig(os.path.join(SAVE_DIR, ten_file), dpi=200)
    plt.close(fig)
    print(f"[+] Đã lưu: {ten_file}")

#Bảng 20 màu rời cách đều: thấp nhất = xanh biển -> giữa = xanh lá -> cao nhất = đỏ
#Chèn vàng/cam giữa xanh lá và đỏ để vùng chuyển không bị nâu (lỗi nội suy RGB)
PALETTE = ["#1f78b4", "#2786a7", "#2e949b", "#36a38e", "#34a473",
           "#31a254", "#2da136", "#46a92d", "#6cb62e", "#93c32f",
           "#afc82e", "#c1c62d", "#d4c32b", "#e2bd29", "#e7af25",
           "#eca221", "#ef8f1e", "#eb681d", "#e7411d", "#e31a1c"]

#Gán mỗi giá trị vào 1 trong 20 bậc màu cách đều nhau trên đoạn [min, max]
def mau_theo_gia_tri(values):
    vmin, vmax = min(values), max(values)
    if vmax == vmin:
        return [PALETTE[len(PALETTE) // 2]] * len(values)
    buoc = (vmax - vmin) / (len(PALETTE) - 1)
    mau = []
    for v in values:
        idx = min(max(int(round((v - vmin) / buoc)), 0), len(PALETTE) - 1)
        mau.append(PALETTE[idx])
    return mau

#Phân tích khám phá dữ liệu (EDA) và xuất 4 biểu đồ ra 4 file PNG riêng
def generate_eda_charts():
    df = get_data_from_sql()
    print(f"[*] Đã tải thành công {len(df)} bài báo từ CSDL.")

    # 1. Tiền xử lý các trường mô tả dữ liệu
    df["content"] = df["content"].fillna("")
    df["word_count"] = df["content"].apply(lambda x: len(x.split()))
    df["author_type"] = df["author"].apply(lambda x: "Chung (VnExpress)" if x in ["VnExpress", "", None] else "Tác giả cụ thể")
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")  # cột đã là DATETIME trong CSDL
    df["hour"] = df["published_at"].dt.hour

    # 2. In Thống kê mô tả ra terminal
    print("\n===== THỐNG KÊ MÔ TẢ =====")
    print(f"Tổng số bài: {len(df)}")
    print(f"Số bài có nội dung rỗng: {(df['word_count'] == 0).sum()}")
    print("\n-- Độ dài bài (word_count) & khung giờ (hour) --")
    print(pd.DataFrame({
        "word_count (số từ/bài)": thong_ke(df["word_count"]),
        "hour (khung giờ)": thong_ke(df["hour"]),
    }).to_string())
    print("\n-- Tần số chuyên mục --")
    print(df["category"].value_counts().to_string())
    print("===========================\n")

    # 3. BIỂU ĐỒ 1: Phân bố chuyên mục (Bar Chart, màu theo mốc least/avg/most)
    fig1, ax1 = plt.subplots(figsize=(9, 6))
    cat_counts = df["category"].value_counts().sort_values(ascending=True)
    bars1 = ax1.barh(cat_counts.index, cat_counts.values, color=mau_theo_gia_tri(cat_counts.values), edgecolor="black", height=0.6)
    ax1.set_title("Phân bố số lượng bài theo chuyên mục", fontsize=13, fontweight="bold")
    ax1.set_xlabel("Số lượng bài viết")
    for b in bars1:
        w = b.get_width()
        ax1.text(w + 0.2, b.get_y() + b.get_height() / 2, f"{int(w)}", va="center", fontsize=9)
    luu_anh(fig1, "bieu_do_1_chuyen_muc.png")

    # 4. BIỂU ĐỒ 2: Phân bố độ dài bài viết (Histogram, màu theo mốc least/avg/most)
    fig2, ax2 = plt.subplots(figsize=(9, 6))
    mean_val = df["word_count"].mean()
    counts, _, patches = ax2.hist(df["word_count"], bins=12, edgecolor="white")
    for c, p in zip(mau_theo_gia_tri(list(counts)), patches):
        p.set_facecolor(c)
    ax2.axvline(mean_val, color="#333333", linestyle="--", linewidth=1.5, label=f"Trung bình: {mean_val:.0f} từ")
    ax2.set_title("Hình thái phân bố độ dài bài báo (số từ)", fontsize=13, fontweight="bold")
    ax2.set_xlabel("Số từ trong bài")
    ax2.set_ylabel("Số lượng bài viết")
    ax2.legend()
    luu_anh(fig2, "bieu_do_2_do_dai.png")

    # 5. BIỂU ĐỒ 3: Tỷ lệ nguồn tác giả (Donut Chart)
    fig3, ax3 = plt.subplots(figsize=(8, 8))
    author_counts = df["author_type"].value_counts()
    _, _, autotexts = ax3.pie(
        author_counts.values, labels=author_counts.index, autopct="%1.1f%%",
        startangle=90, colors=["#4a90e2", "#f5a623"], pctdistance=0.72,
        textprops={"fontsize": 11}, wedgeprops={"width": 0.5, "edgecolor": "white"}
    )
    for at in autotexts:
        at.set_fontsize(11)
        at.set_weight("bold")
    ax3.set_title("Tỷ lệ nguồn tác giả", fontsize=13, fontweight="bold")
    luu_anh(fig3, "bieu_do_3_tac_gia.png")

    # 6. BIỂU ĐỒ 4: Phân bố theo 24 khung giờ xuất bản (Bar Chart, màu theo mốc least/avg/most)
    fig4, ax4 = plt.subplots(figsize=(9, 6))
    hour_series = df["hour"].dropna().astype(int)
    hour_counts = hour_series.value_counts().reindex(range(24), fill_value=0)
    bars4 = ax4.bar(hour_counts.index, hour_counts.values, color=mau_theo_gia_tri(hour_counts.values), edgecolor="black", width=0.7)
    ax4.set_title("Phân bố theo 24 khung giờ xuất bản", fontsize=13, fontweight="bold")
    ax4.set_xlabel("Khung giờ (0h - 23h)")
    ax4.set_ylabel("Số lượng bài đăng")
    ax4.set_xticks(range(0, 24, 2))
    for b in bars4:
        h = b.get_height()
        if h > 0:
            ax4.text(b.get_x() + b.get_width() / 2, h + 0.2, f"{int(h)}", ha="center", fontsize=8)
    luu_anh(fig4, "bieu_do_4_khung_gio.png")

    print("[+] Hoàn tất! Đã xuất 4 biểu đồ ra 4 file PNG riêng.")

if __name__ == "__main__":
    # Khởi chạy phân tích EDA và xuất 4 biểu đồ khi thực thi trực tiếp file
    generate_eda_charts()
