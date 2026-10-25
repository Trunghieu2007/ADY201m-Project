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
from matplotlib.colors import BoundaryNorm, ListedColormap

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
    cur.execute(
        "SELECT article_id, title, description, content, author, published_at, "
        "category, subcategory FROM dbo.VnExpress_Articles"
    )
    cols = [c[0] for c in cur.description]
    df = pd.DataFrame.from_records(cur.fetchall(), columns=cols)
    cur.close()
    conn.close()
    return df

#Bộ thống kê mô tả gọn
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
def luu_anh(fig, ten_file, rect=(0, 0, 1, 1)):
    # rect chừa khoảng trống dưới đáy cho dòng ghi chú (fig.text)
    fig.tight_layout(rect=rect)
    fig.savefig(os.path.join(SAVE_DIR, ten_file), dpi=200, facecolor="white")
    plt.close(fig)
    print(f"[+] Đã lưu: {ten_file}")

#Bảng 20 màu rời cách đều: thấp nhất = xanh biển -> giữa = xanh lá -> cao nhất = đỏ
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

#Định dạng giờ kiểu Việt Nam: 8 -> "8", 8.5 -> "8,5"
def dinh_dang_gio(x):
    return f"{x:.1f}".rstrip("0").rstrip(".").replace(".", ",")

#BIỂU ĐỒ 1: Top 10 chuyên mục con (Bar Chart) - xếp hạng tần số của biến phân loại cấp 2
def ve_bieu_do_1(df):
    sub_all = df["subcategory"].fillna("Không có").str.strip()
    sub_all = sub_all[sub_all.ne("Không có")]
    sub = sub_all.value_counts().head(10).sort_values()
    n_sub = len(sub_all)

    fig1, ax1 = plt.subplots(figsize=(10, 6.5))
    bars1 = ax1.barh(sub.index, sub.values, height=0.65,
                     color=mau_theo_gia_tri(list(sub.values)), edgecolor="black")
    for b in bars1:
        w = int(b.get_width())
        pct = f"{w / n_sub * 100:.1f}".replace(".", ",")
        ax1.text(w + 0.15, b.get_y() + b.get_height() / 2,
                 f"{w}  ({pct}%)", va="center", fontsize=9)
    ax1.set_title("Top 10 chuyên mục con theo số bài", fontsize=13, fontweight="bold")
    ax1.set_xlabel("Số lượng bài viết")
    ax1.set_xlim(0, sub.max() * 1.22)
    ax1.set_xticks(range(0, int(sub.max()) + 2))
    ax1.grid(axis="x", linestyle=":", alpha=0.45)
    ax1.set_axisbelow(True)
    fig1.text(0.5, 0.015,
              f"Tính trên {n_sub}/{len(df)} bài có subcategory; "
              f"{len(df) - n_sub} bài ghi 'Không có' không được vẽ",
              ha="center", fontsize=9, color="#444444")
    luu_anh(fig1, "bieu_do_1_chuyen_muc_con.png", rect=[0, 0.04, 1, 1])

#BIỂU ĐỒ 2: Số bài lũy kế theo giờ (Line Chart / ECDF bậc thang) - đọc phân vị trực tiếp trên đường
def ve_bieu_do_2(df):
    hour_all = df["hour"].dropna().astype(int)
    hour_counts = hour_all.value_counts().reindex(range(24), fill_value=0)
    cum_pct = hour_counts.cumsum() / len(hour_all) * 100
    hours = np.arange(24)
    last_hour = int(hour_all.max())
    thieu_gio = int(df["published_at"].isna().sum())
    t_min = df["published_at"].min()
    t_max = df["published_at"].max()

    fig2, ax2 = plt.subplots(figsize=(10, 6.5))
    ax2.plot(hours, cum_pct, drawstyle="steps-post", color="#1f78b4",
             linewidth=2.2, marker="o", markersize=4, label="Số bài lũy kế")
    ax2.fill_between(hours, 0, cum_pct, step="post", color="#1f78b4", alpha=0.10)
    p50 = hour_all.quantile(0.5)
    p80 = hour_all.quantile(0.8)
    for x, label in [(p50, f"Trung vị: {dinh_dang_gio(p50)}h"),
                     (p80, f"P80: {dinh_dang_gio(p80)}h")]:
        ax2.axvline(x, color="#e31a1c", linestyle="--", linewidth=1.3)
        ax2.text(x + 0.25, 8, label, color="#e31a1c", fontsize=9, rotation=90)
    ax2.annotate(f"{len(hour_all)} bài (100%)", xy=(last_hour, 100),
                 xytext=(min(last_hour + 1.2, 16), 78),
                 fontsize=9, color="#333333",
                 arrowprops={"arrowstyle": "->", "color": "#666666", "lw": 1})
    ax2.set_title(f"Số bài xuất bản lũy kế theo giờ (n={len(hour_all)})",
                  fontsize=13, fontweight="bold")
    ax2.set_xlabel("Khung giờ trong ngày")
    ax2.set_ylabel("% số bài lũy kế")
    ax2.set_xticks(range(0, 24, 2))
    ax2.set_xlim(0, 23)
    ax2.set_ylim(0, 108)
    ax2.grid(linestyle=":", alpha=0.45)
    ax2.set_axisbelow(True)
    ax2.legend(loc="lower right", fontsize=9)
    fig2.text(0.5, 0.015,
              f"Dữ liệu phủ {t_min:%d/%m %H:%M} - {t_max:%d/%m %H:%M}; "
              f"{thieu_gio} bài thiếu published_at. "
              "Đường ngang sau giờ cuối phản ánh phạm vi dữ liệu, không phải nhịp đăng thực tế.",
              ha="center", fontsize=8.5, color="#444444")
    luu_anh(fig2, "bieu_do_2_luy_ke_gio.png", rect=[0, 0.045, 1, 1])

#BIỂU ĐỒ 3: Quan hệ độ dài mô tả và độ dài nội dung (Scatter Plot) - tương quan hai biến định lượng
def ve_bieu_do_3(df):
    valid = df[(df["desc_wc"] > 0) & (df["word_count"] > 0)]
    empty_content = df[df["word_count"] == 0]
    empty_desc = df[(df["desc_wc"] == 0) & (df["word_count"] > 0)]
    r_all = df["desc_wc"].corr(df["word_count"])
    r_valid = valid["desc_wc"].corr(valid["word_count"])
    rho_valid = valid["desc_wc"].corr(valid["word_count"], method="spearman")

    fig3, ax3 = plt.subplots(figsize=(10, 7))
    ax3.scatter(valid["desc_wc"], valid["word_count"], s=48, color="#1f78b4",
                alpha=0.65, edgecolor="white", linewidth=0.6,
                label=f"Đủ dữ liệu (n={len(valid)})", zorder=2)
    if len(empty_content):
        ax3.scatter(empty_content["desc_wc"], np.zeros(len(empty_content)), s=70,
                    color="#e31a1c", edgecolor="white", linewidth=0.6,
                    label=f"Rỗng nội dung (n={len(empty_content)})", zorder=4)
    if len(empty_desc):
        ax3.scatter(empty_desc["desc_wc"], empty_desc["word_count"], s=70,
                    color="#f5a623", edgecolor="white", linewidth=0.6,
                    label=f"Rỗng mô tả (n={len(empty_desc)})", zorder=4)
    if len(valid) > 1:
        coef = np.polyfit(valid["desc_wc"], valid["word_count"], 1)
        xline = np.linspace(valid["desc_wc"].min(), valid["desc_wc"].max(), 50)
        ax3.plot(xline, np.polyval(coef, xline), color="#666666",
                 linestyle="--", linewidth=1.3, label="Xu hướng tuyến tính")

    ax3.text(0.98, 0.96,
             f"Pearson r = {r_valid:.3f}".replace(".", ",") + f" (n={len(valid)})\n"
             f"Spearman ρ = {rho_valid:.3f}".replace(".", ",") + "\n"
             f"Pearson r = {r_all:.3f}".replace(".", ",") + f" (cả {len(df)} bài)",
             transform=ax3.transAxes, ha="right", va="top", fontsize=9,
             bbox={"facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9})
    ax3.set_title("Độ dài mô tả và độ dài nội dung bài báo", fontsize=13, fontweight="bold")
    ax3.set_xlabel("Số từ trong mô tả (description)")
    ax3.set_ylabel("Số từ trong nội dung (content)")
    ax3.set_ylim(bottom=-50)
    ax3.grid(linestyle=":", alpha=0.4)
    ax3.set_axisbelow(True)
    ax3.legend(loc="lower right", fontsize=8.5)
    # Kết luận theo độ mạnh tuyệt đối của Pearson r
    if abs(r_valid) < 0.1:
        muc_do = "Gần như không có tương quan tuyến tính"
    elif abs(r_valid) < 0.3:
        muc_do = "Tương quan yếu"
    elif abs(r_valid) < 0.5:
        muc_do = "Tương quan trung bình"
    else:
        muc_do = "Tương quan mạnh"
    fig3.text(0.5, 0.015,
              f"{muc_do}: độ dài sa-pô không dự báo được độ dài bài; tương quan không phải nhân quả",
              ha="center", fontsize=9, color="#444444")
    luu_anh(fig3, "bieu_do_3_mo_ta_noi_dung.png", rect=[0, 0.04, 1, 1])

#BIỂU ĐỒ 4: Cơ cấu nguồn tác giả theo chuyên mục (Stacked Bar 100%) - P(author_type | category)
def ve_bieu_do_4(df):
    ct = pd.crosstab(df["category"], df["author_type"])
    for col in ["Tác giả cụ thể", "Chung (VnExpress)"]:
        if col not in ct:
            ct[col] = 0
    ct = ct[["Tác giả cụ thể", "Chung (VnExpress)"]]
    ct["n"] = ct.sum(axis=1)
    ct["pct_chung"] = ct["Chung (VnExpress)"] / ct["n"] * 100
    ct = ct.sort_values("pct_chung")
    pct = ct[["Tác giả cụ thể", "Chung (VnExpress)"]].div(ct["n"], axis=0) * 100

    fig4, ax4 = plt.subplots(figsize=(10, 7.5))
    labels = [f"{cat} ({int(n)})" for cat, n in zip(ct.index, ct["n"])]
    ax4.barh(labels, pct["Tác giả cụ thể"], height=0.68,
             color="#4a90e2", label="Tác giả cụ thể", edgecolor="white")
    ax4.barh(labels, pct["Chung (VnExpress)"], left=pct["Tác giả cụ thể"], height=0.68,
             color="#f5a623", label="Chung (VnExpress)", edgecolor="white")
    for i, pct_chung in enumerate(ct["pct_chung"]):
        if pct_chung >= 10:
            ax4.text(100 - pct_chung / 2, i, f"{pct_chung:.0f}%", ha="center",
                     va="center", fontsize=8, color="#333333", fontweight="bold")
    ax4.set_title("Cơ cấu nguồn tác giả trong từng chuyên mục (100%)",
                  fontsize=13, fontweight="bold", pad=34)
    ax4.set_xlabel("Tỷ lệ % số bài trong chuyên mục")
    ax4.set_xlim(0, 100)
    ax4.grid(axis="x", linestyle=":", alpha=0.4)
    ax4.set_axisbelow(True)
    ax4.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2,
               fontsize=9, frameon=False)
    n_chung = int((df["author_type"] == "Chung (VnExpress)").sum())
    pct_chung_all = f"{n_chung / len(df) * 100:.1f}".replace(".", ",")
    fig4.text(0.5, 0.015,
              f"{n_chung}/{len(df)} bài ({pct_chung_all}%) dùng byline chung VnExpress; "
              "'VnExpress' có thể là giá trị mặc định khi thiếu byline",
              ha="center", fontsize=8.5, color="#444444")
    luu_anh(fig4, "bieu_do_4_tac_gia_chuyen_muc.png", rect=[0, 0.04, 1, 1])

#BIỂU ĐỒ 5: Nhiệt đồ chuyên mục x khung giờ (Heatmap) - tần số kết hợp của hai biến định tính
def ve_bieu_do_5(df):
    # Ngưỡng tối thiểu co giãn theo cỡ mẫu: 102 bài -> 6, 45 bài -> 4
    nguong = max(4, int(round(len(df) * 0.06)))
    cat_counts = df["category"].value_counts()
    top_cats = [c for c in cat_counts.index
                if c != "Khác" and cat_counts[c] >= nguong][:9]
    if not top_cats:  # mẫu quá nhỏ: vẫn lấy các chuyên mục có bài, trừ "Khác"
        top_cats = [c for c in cat_counts.index if c != "Khác"][:9]
    df_time = df.dropna(subset=["hour"]).copy()
    df_time["hour"] = df_time["hour"].astype(int)
    hours = list(range(int(df_time["hour"].min()), int(df_time["hour"].max()) + 1))
    heat = pd.crosstab(df_time["category"], df_time["hour"]).reindex(
        index=top_cats, columns=hours, fill_value=0
    )
    vmax = int(heat.values.max())
    colors = ["#f2f2f2"] + [PALETTE[i] for i in
                            np.linspace(0, len(PALETTE) - 1, vmax).astype(int)]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(np.arange(-0.5, vmax + 1.5, 1), cmap.N)

    fig5, ax5 = plt.subplots(figsize=(12, 6.8))
    ax5.imshow(heat.values, aspect="auto", cmap=cmap, norm=norm)
    ax5.set_xticks(range(heat.shape[1]))
    ax5.set_xticklabels([f"{h}h" for h in heat.columns])
    ax5.set_yticks(range(len(top_cats)))
    ax5.set_yticklabels([f"{c} ({int((df['category'] == c).sum())})" for c in top_cats])
    ax5.set_xlabel("Khung giờ xuất bản")
    ax5.set_ylabel("Chuyên mục (số bài)")
    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]):
            v = int(heat.iloc[i, j])
            if v > 0:
                # Chọn màu chữ đen/trắng theo độ sáng của ô để luôn đọc được số
                r_, g_, b_ = (int(colors[v][k:k + 2], 16) / 255 for k in (1, 3, 5))
                lum = 0.299 * r_ + 0.587 * g_ + 0.114 * b_
                ax5.text(j, i, str(v), ha="center", va="center", fontsize=9,
                         color="#222222" if lum > 0.55 else "white",
                         fontweight="bold" if v >= 3 else "normal")
    ax5.set_xticks(np.arange(-0.5, heat.shape[1], 1), minor=True)
    ax5.set_yticks(np.arange(-0.5, heat.shape[0], 1), minor=True)
    ax5.grid(which="minor", color="white", linewidth=2)
    ax5.tick_params(which="minor", length=0)
    ax5.set_title("Số bài theo chuyên mục và khung giờ xuất bản",
                  fontsize=13, fontweight="bold")
    n_time = int(len(df_time))
    thieu_gio = int(df["published_at"].isna().sum())
    fig5.text(0.5, 0.015,
              f"{len(top_cats)} chuyên mục chính có ≥{nguong} bài (không tính Khác); "
              f"{n_time} bài có timestamp, bỏ {thieu_gio} bài thiếu giờ. "
              "Ô trống = 0 bài. Màu chuyển từ xanh (ít) sang đỏ (nhiều); đây là RSS snapshot, không phải lịch tòa soạn.",
              ha="center", fontsize=8.5, color="#444444")
    luu_anh(fig5, "bieu_do_5_nhiet_do_chuyen_muc_gio.png", rect=[0, 0.04, 1, 1])

#Phân tích khám phá dữ liệu (EDA) và xuất 5 biểu đồ ra 5 file PNG riêng
def generate_eda_charts():
    df = get_data_from_sql()
    print(f"[*] Đã tải thành công {len(df)} bài báo từ CSDL.")
    if df.empty:
        print("[!] Bảng dữ liệu đang rỗng, không thể vẽ biểu đồ.")
        return

    # 1. Tiền xử lý các trường mô tả dữ liệu
    df["content"] = df["content"].fillna("")
    df["description"] = df["description"].fillna("")
    df["word_count"] = df["content"].apply(lambda x: len(x.split()))
    df["desc_wc"] = df["description"].apply(lambda x: len(x.split()))
    df["author_type"] = df["author"].apply(lambda x: "Chung (VnExpress)" if x in ["VnExpress", "", None] else "Tác giả cụ thể")
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    df["hour"] = df["published_at"].dt.hour

    # 2. In Thống kê mô tả ra terminal
    print("\n===== THỐNG KÊ MÔ TẢ =====")
    print(f"Tổng số bài: {len(df)}")
    print(f"Số bài có nội dung rỗng: {(df['word_count'] == 0).sum()}")
    print(f"Số bài có mô tả rỗng: {(df['desc_wc'] == 0).sum()}")
    print(f"Số bài thiếu published_at: {df['published_at'].isna().sum()}")
    print("\n-- Độ dài bài (word_count) & khung giờ (hour) --")
    print(pd.DataFrame({
        "word_count (số từ/bài)": thong_ke(df["word_count"]),
        "hour (khung giờ)": thong_ke(df["hour"]),
    }).to_string())
    print("\n-- Tần số chuyên mục --")
    print(df["category"].value_counts().to_string())
    print("===========================\n")

    # 3. Xuất 5 biểu đồ: 2 biểu đồ một biến và 3 biểu đồ quan hệ/cơ cấu
    ve_bieu_do_1(df)
    ve_bieu_do_2(df)
    ve_bieu_do_3(df)
    ve_bieu_do_4(df)
    ve_bieu_do_5(df)

    print("[+] Hoàn tất! Đã xuất 5 biểu đồ ra 5 file PNG riêng.")

if __name__ == "__main__":
    # Khởi chạy phân tích EDA và xuất 5 biểu đồ khi thực thi trực tiếp file
    generate_eda_charts()
