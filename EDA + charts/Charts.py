import os
import sys
# pyrefly: ignore[missing-import]
import pyodbc  # type: ignore
# pyrefly: ignore[missing-import]
import pandas as pd  # type: ignore
# pyrefly: ignore[missing-import]
import numpy as np  # type: ignore
# pyrefly: ignore[missing-import]
import matplotlib.pyplot as plt  # type: ignore
from matplotlib.colors import ListedColormap

# Đảm bảo hiển thị tiếng Việt chuẩn trên Console và Biểu đồ
sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# Thư mục lưu file biểu đồ đầu ra (cùng thư mục với script này)
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))

#Bảng 20 màu rời cách đều: thấp nhất = xanh biển -> giữa = xanh lá -> cao nhất = đỏ
PALETTE = ["#1f78b4", "#2685a8", "#2d939c", "#319b8a", "#33a277",
           "#31a35d", "#2ea140", "#41a833", "#5fb230", "#7ebb2e",
           "#9dc32e", "#b7c72d", "#c8c52c", "#d8be29", "#e3ae25",
           "#ec9c21", "#eb801f", "#eb641d", "#e73f1c", "#e31a1c"]

#get_data_from_sql: truy vấn dữ liệu bài báo từ SQL Server và trả về pandas DataFrame
def get_data_from_sql():
    conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\\SQLEXPRESS;DATABASE=ADY201m;Trusted_Connection=yes;"
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()
    cur.execute(
        "SELECT article_id, title, description, content, author, published_at, "
        "category, subcategory FROM dbo.VnExpress_Articles"
    )
    df = pd.DataFrame.from_records(cur.fetchall(), columns=[c[0] for c in cur.description])
    cur.close()
    conn.close()
    return df

#mau_theo_gia_tri: gán mỗi giá trị vào 1 trong 20 bậc màu cách đều trên đoạn [min, max]
def mau_theo_gia_tri(values):
    vmin, vmax = min(values), max(values)
    if vmax == vmin:
        return [PALETTE[len(PALETTE) // 2]] * len(values)
    return [PALETTE[int(round((v - vmin) / (vmax - vmin) * (len(PALETTE) - 1)))]
            for v in values]

#luu_anh: lưu một figure ra PNG riêng rồi đóng lại; rect tuỳ chọn để thu nhỏ/căn giữa vùng vẽ
def luu_anh(fig, ten_file, rect=(0, 0, 1, 1)):
    fig.tight_layout(rect=rect)
    fig.savefig(os.path.join(SAVE_DIR, ten_file), dpi=200, facecolor="white")
    plt.close(fig)
    print(f"[+] Đã lưu: {ten_file}")

#ve_bieu_do_1: số bài theo chuyên mục, bar ngang tô màu động theo giá trị
def ve_bieu_do_1(df):
    cat = df["category"].fillna("Khác").str.strip().value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(cat.index, cat.values, edgecolor="black",
                   color=mau_theo_gia_tri(list(cat.values)))
    for b, v in zip(bars, cat.values):
        pct = f"{v / len(df) * 100:.1f}".replace(".", ",")
        ax.text(v + 0.15, b.get_y() + b.get_height() / 2,
                f"{v}  ({pct}%)", va="center", fontsize=9)
    ax.set_title(f"Số bài theo chuyên mục (n={len(df)})", fontsize=13, fontweight="bold")
    ax.set_xlabel("Số lượng bài viết")
    ax.set_xlim(0, cat.max() * 1.18)
    ax.grid(axis="x", linestyle=":", alpha=0.45)
    ax.set_axisbelow(True)
    luu_anh(fig, "bieu_do_1_chuyen_muc.png")

#ve_bieu_do_2: histogram số bài theo 24 khung giờ trong ngày, màu động theo tần số
def ve_bieu_do_2(df):
    hour = df["hour"].dropna().astype(int)
    dem = hour.value_counts().reindex(range(24), fill_value=0)
    fig, ax = plt.subplots(figsize=(13, 6.5))
    bars = ax.bar(dem.index, dem.values, width=0.82, edgecolor="black",
                  color=mau_theo_gia_tri(list(dem.values)))
    for b, v in zip(bars, dem.values):
        if v:
            ax.text(b.get_x() + b.get_width() / 2, v + 0.2, int(v),
                    ha="center", va="bottom", fontsize=9)
    ax.set_title(f"Số bài xuất bản theo khung giờ (n={len(hour)})",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Khung giờ trong ngày")
    ax.set_ylabel("Số bài viết")
    ticks = [f"{h}h" for h in range(24)]
    ax.set_xticks(range(24), ticks)
    ax.tick_params(axis="x", labelsize=8)
    ax.set_xlim(-0.6, 23.6)
    ax.set_ylim(0, dem.max() * 1.18)
    ax.grid(axis="y", linestyle=":", alpha=0.45)
    ax.set_axisbelow(True)
    luu_anh(fig, "bieu_do_2_phan_bo_gio.png")

#ve_bieu_do_3: pie chart cơ cấu tác giả, chỉ tách VnExpress và nhóm còn lại
def ve_bieu_do_3(df):
    author = df["author"].fillna("VnExpress").str.strip()
    vne = int((author == "VnExpress").sum())
    vals = [vne, len(author) - vne]
    labels = ["VnExpress", "Các tác giả khác"]
    colors = ["#1f78b4", "#bdbdbd"]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.pie(vals, labels=labels, colors=colors, startangle=90,
           counterclock=False, pctdistance=0.7,
           autopct=lambda p: f"{p:.1f}%".replace(".", ","),
           wedgeprops={"edgecolor": "white", "linewidth": 1.5},
           textprops={"fontsize": 10})
    ax.set_title(f"Cơ cấu tác giả bài viết (n={len(df)})",
                 fontsize=13, fontweight="bold")
    luu_anh(fig, "bieu_do_3_tac_gia.png")

#ve_bieu_do_4: heatmap chuyên mục x khung giờ, màu động theo tần số
def ve_bieu_do_4(df):
    counts = df["category"].value_counts()
    nguong = max(4, round(len(df) * 0.06))
    top = [c for c in counts.index if c != "Khác" and counts[c] >= nguong][:9]
    top = top or list(counts.index[:9])
    hours = range(24)
    heat = pd.crosstab(df["category"], df["hour"]).reindex(
        index=top, columns=hours, fill_value=0
    )
    vmax = int(heat.values.max())
    colors = ["#f2f2f2"] + mau_theo_gia_tri(list(range(1, vmax + 1)))

    fig, ax = plt.subplots(figsize=(15, 5.6))
    ax.imshow(heat.values, aspect="auto", cmap=ListedColormap(colors),
              vmin=-0.5, vmax=vmax + 0.5)
    ax.set_xticks(range(len(hours)), [f"{h}h" for h in hours])
    ax.tick_params(axis="x", labelsize=8)
    ax.set_yticks(range(len(top)), [f"{c} ({int(counts[c])})" for c in top])
    ax.set_xlabel("Khung giờ xuất bản")
    ax.set_ylabel("Chuyên mục (số bài)")
    for i, row in enumerate(heat.values):
        for j, v in enumerate(row):
            if v:
                ax.text(j, i, int(v), ha="center", va="center",
                        color="white", fontsize=9, fontweight="bold")
    ax.set_xticks(np.arange(-0.5, len(hours), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(top), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)
    ax.set_title("Số bài theo chuyên mục và khung giờ xuất bản",
                 fontsize=12.5, fontweight="bold")
    # rect thu nhỏ vùng vẽ và giữ heatmap ở giữa khung ảnh
    luu_anh(fig, "bieu_do_4_nhiet_do_chuyen_muc_gio.png", rect=[0.16, 0.16, 0.84, 0.86])

#generate_eda_charts: phân tích khám phá dữ liệu (EDA) và xuất 4 biểu đồ ra 4 file PNG riêng
def generate_eda_charts():
    df = get_data_from_sql()
    print(f"[*] Đã tải thành công {len(df)} bài báo từ CSDL.")
    if df.empty:
        print("[!] Bảng dữ liệu đang rỗng, không thể vẽ biểu đồ.")
        return

    # 1. Tiền xử lý các trường mô tả dữ liệu
    df["content"] = df["content"].fillna("")
    df["description"] = df["description"].fillna("")
    df["word_count"] = df["content"].str.split().str.len()
    df["desc_wc"] = df["description"].str.split().str.len()
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    df["hour"] = df["published_at"].dt.hour

    # 2. In Thống kê mô tả ra terminal
    print("\n===== THỐNG KÊ MÔ TẢ =====")
    print(f"Tổng số bài: {len(df)}")
    print(f"Số bài có nội dung rỗng: {(df['word_count'] == 0).sum()}")
    print(f"Số bài có mô tả rỗng: {(df['desc_wc'] == 0).sum()}")
    print(f"Số bài thiếu published_at: {df['published_at'].isna().sum()}")
    print("\n-- Độ dài bài (word_count) & khung giờ (hour) --")
    print(df[["word_count", "hour"]].describe()
          .loc[["count", "mean", "std", "min", "max"]].round(2).to_string())
    print("\n-- Tần số chuyên mục --")
    print(df["category"].value_counts().to_string())
    print("===========================\n")

    # 3. Xuất 4 biểu đồ: 2 biểu đồ một biến và 2 biểu đồ quan hệ
    ve_bieu_do_1(df)
    ve_bieu_do_2(df)
    ve_bieu_do_3(df)
    ve_bieu_do_4(df)

    print("[+] Hoàn tất! Đã xuất 4 biểu đồ ra 4 file PNG riêng.")

if __name__ == "__main__":
    # Khởi chạy phân tích EDA và xuất 4 biểu đồ khi thực thi trực tiếp file
    generate_eda_charts()
