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

#Phân tích khám phá dữ liệu (EDA) và xuất dashboard 4 biểu đồ tổng hợp ra file ảnh
def generate_eda_charts():
    df = get_data_from_sql()
    print(f"[*] Đã tải thành công {len(df)} bài báo từ CSDL.")

    # 1. Tiền xử lý các trường mô tả dữ liệu
    df["word_count"] = df["content"].fillna("").apply(lambda x: len(x.split()))
    df["author_type"] = df["author"].apply(lambda x: "Chung (VnExpress)" if x in ["VnExpress", "", None] else "Tác giả cụ thể")
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")  # cột đã là DATETIME trong CSDL
    df["hour"] = df["published_at"].dt.hour

    # 2. In Thống kê mô tả (Count / Mean / Min / Max / Quantiles + tần số chuyên mục)
    print("\n===== THỐNG KÊ MÔ TẢ =====")
    print(f"Tổng số bài: {len(df)}")
    print("\n-- Độ dài bài (word_count) & khung giờ (hour) --")
    print(df[["word_count", "hour"]].describe().to_string())
    print("\n-- Tần số chuyên mục --")
    print(df["category"].value_counts().to_string())
    print("===========================\n")

    # ========================================================
    # BIỂU ĐỒ TỔNG HỢP DUY NHẤT (Dashboard 2x2: 4 trong 1)
    # ========================================================
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle("TỔNG HỢP MÔ TẢ DỮ LIỆU BÁO CHÍ VNEXPRESS", fontsize=16, fontweight="bold", y=0.98)

    # 1. Bar Chart: Phân bố chuyên mục
    cat_counts = df["category"].value_counts().sort_values(ascending=True)
    bars1 = axes[0, 0].barh(cat_counts.index, cat_counts.values, color="#3470a3", edgecolor="black", height=0.6)
    axes[0, 0].set_title("1. Phân bố chuyên mục (Số bài)", fontsize=12, fontweight="bold")
    axes[0, 0].set_xlabel("Số lượng bài viết")
    for b in bars1:
        w = b.get_width()
        axes[0, 0].text(w + 0.2, b.get_y() + b.get_height()/2, f"{int(w)}", va="center", fontsize=9)

    # 2. Histogram: Phân bố độ dài bài viết (Số từ)
    mean_val = df["word_count"].mean()
    axes[0, 1].hist(df["word_count"], bins=12, color="#48997a", edgecolor="white")
    axes[0, 1].axvline(mean_val, color="red", linestyle="--", linewidth=1.5, label=f"Trung bình: {mean_val:.0f} từ")
    axes[0, 1].set_title("2. Phân bố độ dài bài báo (Số từ)", fontsize=12, fontweight="bold")
    axes[0, 1].set_xlabel("Số từ trong bài")
    axes[0, 1].set_ylabel("Số lượng bài viết")
    axes[0, 1].legend()

    # 3. Donut Chart: Tỷ lệ tác giả
    author_counts = df["author_type"].value_counts()
    wedges, texts, autotexts = axes[1, 0].pie(
        author_counts.values, labels=author_counts.index, autopct="%1.1f%%",
        startangle=90, colors=["#4a90e2", "#f5a623"], pctdistance=0.72,
        textprops={"fontsize": 11}, wedgeprops={"width": 0.5, "edgecolor": "white"}
    )
    for at in autotexts:
        at.set_fontsize(11)
        at.set_weight("bold")
    axes[1, 0].set_title("3. Tỷ lệ nguồn tác giả", fontsize=12, fontweight="bold")

    # 4. Bar Chart: Khung giờ xuất bản (24h)
    hour_series = df["hour"].dropna().astype(int)
    hour_counts = hour_series.value_counts().reindex(range(24), fill_value=0)
    bars4 = axes[1, 1].bar(hour_counts.index, hour_counts.values, color="#9055a2", edgecolor="black", width=0.7)
    axes[1, 1].set_title("4. Phân bố theo 24 khung giờ xuất bản", fontsize=12, fontweight="bold")
    axes[1, 1].set_xlabel("Khung giờ (0h - 23h)")
    axes[1, 1].set_ylabel("Số lượng bài đăng")
    axes[1, 1].set_xticks(range(0, 24, 2))
    for b in bars4:
        h = b.get_height()
        if h > 0:
            axes[1, 1].text(b.get_x() + b.get_width()/2, h + 0.2, f"{int(h)}", ha="center", fontsize=8)

    # Đường dẫn lưu file ảnh tổng hợp kết quả
    output_path = os.path.join(SAVE_DIR, "tong_hop_4_bieu_do.png")
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"[+] Hoàn tất! Đã lưu biểu đồ tổng hợp tại: {output_path}")

if __name__ == "__main__":
    # Khởi chạy phân tích EDA và xuất biểu đồ khi thực thi trực tiếp file
    generate_eda_charts()
