"""Vẽ sơ đồ quan hệ thực thể (ERD) Microsoft SQL Server 3NF chất lượng cao cho ADY201m."""
from __future__ import annotations

import sys
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path as MplPath

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_IMAGE = PROJECT_ROOT / "outputs" / "database" / "erd_diagram.png"


def draw_erd() -> Path:
    # Kích thước canvas
    fig, ax = plt.subplots(figsize=(19, 13), dpi=300)
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")
    ax.set_xlim(0, 1900)
    ax.set_ylim(0, 1300)
    ax.axis("off")

    # Tiêu đề chính của sơ đồ
    ax.text(
        950, 1250,
        "ADY201m — Microsoft SQL Server Database Schema (Chuẩn 3NF)",
        ha="center", va="center", fontsize=21, fontweight="bold", color="#0f172a"
    )
    ax.text(
        950, 1215,
        "Lược đồ thực thể quan hệ (Entity-Relationship Diagram - ERD) 5 Bảng Chuẩn hóa & 13 Đặc trưng Mô tả",
        ha="center", va="center", fontsize=12.5, color="#475569"
    )

    # Định nghĩa cấu trúc các bảng (Đã căn chỉnh cân đối 2 lề 140px)
    tables = {
        "Categories": {
            "title": "dbo.Categories (Chuyên mục)",
            "x": 130, "y": 880, "w": 380, "h": 160,
            "header_color": "#1e40af",
            "columns": [
                ("PK", "category_id", "INT IDENTITY", True, False),
                ("UQ", "name", "NVARCHAR(100)", False, False),
            ]
        },
        "Subcategories": {
            "title": "dbo.Subcategories (Tiểu mục)",
            "x": 130, "y": 570, "w": 380, "h": 200,
            "header_color": "#0369a1",
            "columns": [
                ("PK", "subcategory_id", "INT IDENTITY", True, False),
                ("FK", "category_id", "INT", False, True),
                ("  ", "name", "NVARCHAR(100)", False, False),
            ]
        },
        "Authors": {
            "title": "dbo.Authors (Tác giả)",
            "x": 130, "y": 280, "w": 380, "h": 160,
            "header_color": "#047857",
            "columns": [
                ("PK", "author_id", "INT IDENTITY", True, False),
                ("UQ", "name", "NVARCHAR(255)", False, False),
            ]
        },
        "Articles": {
            "title": "dbo.Articles (Bài viết VnExpress)",
            "x": 670, "y": 200, "w": 470, "h": 700,
            "header_color": "#334155",
            "columns": [
                ("PK", "article_id", "NVARCHAR(50)", True, False),
                ("UQ", "url", "NVARCHAR(1000)", False, False),
                ("  ", "title", "NVARCHAR(1000)", False, False),
                ("  ", "description", "NVARCHAR(MAX)", False, False),
                ("  ", "content", "NVARCHAR(MAX)", False, False),
                ("FK", "author_id", "INT (NULL)", False, True),
                ("  ", "publisher", "NVARCHAR(255)", False, False),
                ("  ", "published_at", "DATETIMEOFFSET(0)", False, False),
                ("FK", "category_id", "INT", False, True),
                ("FK", "subcategory_id", "INT (NULL)", False, True),
                ("  ", "crawled_at", "DATETIMEOFFSET(0)", False, False),
                ("  ", "source", "NVARCHAR(100)", False, False),
                ("  ", "created_at", "DATETIME2(0)", False, False),
                ("  ", "updated_at", "DATETIME2(0)", False, False),
            ]
        },
        "ArticleFeatures": {
            "title": "dbo.ArticleFeatures (13 Đặc trưng Mô tả)",
            "x": 1280, "y": 140, "w": 490, "h": 760,
            "header_color": "#7c3aed",
            "columns": [
                ("PK,FK", "article_id", "NVARCHAR(50)", True, True),
                ("  ", "char_count", "INT", False, False),
                ("  ", "word_count", "INT", False, False),
                ("  ", "sentence_count", "INT", False, False),
                ("  ", "unique_word_count", "INT", False, False),
                ("  ", "lexical_diversity", "FLOAT", False, False),
                ("  ", "avg_word_length", "FLOAT", False, False),
                ("  ", "title_char_count", "INT", False, False),
                ("  ", "title_word_count", "INT", False, False),
                ("  ", "description_char_count", "INT", False, False),
                ("  ", "description_word_count", "INT", False, False),
                ("  ", "title_to_content_word_ratio", "FLOAT", False, False),
                ("  ", "publication_hour", "INT", False, False),
                ("  ", "publication_weekday", "INT", False, False),
                ("  ", "created_at", "DATETIME2(0)", False, False),
                ("  ", "updated_at", "DATETIME2(0)", False, False),
            ]
        }
    }

    # Vẽ từng bảng
    for tbl_name, info in tables.items():
        x, y, w, h = info["x"], info["y"], info["w"], info["h"]
        header_h = 42

        # Khung nền toàn bảng (shadow + border)
        shadow = FancyBboxPatch((x + 4, y - 4), w, h, boxstyle="round,pad=3,rounding_size=8",
                                fc="#cbd5e1", ec="none", zorder=1)
        ax.add_patch(shadow)

        body = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=3,rounding_size=8",
                              fc="#ffffff", ec="#94a3b8", lw=1.5, zorder=2)
        ax.add_patch(body)

        # Thanh tiêu đề (Header bar)
        header = FancyBboxPatch((x, y + h - header_h), w, header_h,
                                boxstyle="round,pad=0,rounding_size=8",
                                fc=info["header_color"], ec="none", zorder=3)
        ax.add_patch(header)
        ax.fill([x, x + w, x + w, x], [y + h - header_h, y + h - header_h, y + h - header_h + 10, y + h - header_h + 10],
                color=info["header_color"], zorder=3)

        # Text tiêu đề bảng
        ax.text(x + w / 2, y + h - (header_h / 2), info["title"],
                ha="center", va="center", color="#ffffff", fontsize=11, fontweight="bold", zorder=4)

        # Vẽ từng cột
        cols = info["columns"]
        row_h = (h - header_h - 10) / len(cols)

        for idx, (badge, col_name, col_type, is_pk, is_fk) in enumerate(cols):
            curr_y = y + h - header_h - 15 - (idx * row_h)

            # Highlight sọc chẵn lẻ
            if idx % 2 == 1:
                ax.fill([x + 1, x + w - 1, x + w - 1, x + 1],
                        [curr_y - row_h / 2 + 3, curr_y - row_h / 2 + 3, curr_y + row_h / 2 - 3, curr_y + row_h / 2 - 3],
                        color="#f1f5f9", zorder=2.5)

            # Badge PK / FK / UQ
            badge_color = "#f8fafc"
            badge_text_color = "#64748b"
            if is_pk and is_fk:
                badge_color = "#fef3c7"
                badge_text_color = "#b45309"
            elif is_pk:
                badge_color = "#fef3c7"
                badge_text_color = "#b45309"
            elif is_fk:
                badge_color = "#e0f2fe"
                badge_text_color = "#0369a1"
            elif badge.strip() == "UQ":
                badge_color = "#f3e8ff"
                badge_text_color = "#7e22ce"

            if badge.strip():
                bbox_props = dict(boxstyle="round,pad=0.2,rounding_size=3", fc=badge_color, ec="none")
                ax.text(x + 12, curr_y, badge, fontsize=8, fontweight="bold", color=badge_text_color,
                        va="center", bbox=bbox_props, zorder=4)

            # Tên cột
            col_weight = "bold" if (is_pk or is_fk) else "normal"
            col_color = "#0f172a" if (is_pk or is_fk) else "#334155"
            ax.text(x + 58, curr_y, col_name, fontsize=9.5, fontweight=col_weight, color=col_color,
                    va="center", zorder=4)

            # Kiểu dữ liệu
            ax.text(x + w - 12, curr_y, col_type, fontsize=8.5, color="#64748b",
                    ha="right", va="center", zorder=4)

    # Hàm vẽ đường nối quan hệ
    def draw_connector(start_pt, end_pt, label="", card_start="1", card_end="N", color="#2563eb", waypoints=None, label_offset_y=12):
        verts = [start_pt]
        if waypoints:
            verts.extend(waypoints)
        verts.append(end_pt)
        codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(verts) - 1)
        path = MplPath(verts, codes)
        patch = PathPatch(path, facecolor="none", edgecolor=color, lw=2.2, zorder=5, linestyle="-")
        ax.add_patch(patch)

        # Vẽ điểm neo đầu tròn và mũi tên kết thúc
        ax.plot(start_pt[0], start_pt[1], "o", color=color, markersize=5, zorder=6)
        ax.plot(end_pt[0], end_pt[1], ">" if end_pt[0] > verts[-2][0] else ("<" if end_pt[0] < verts[-2][0] else "v"),
                color=color, markersize=6, zorder=6)

        # Label quan hệ
        if label:
            if waypoints:
                mid_x = waypoints[0][0]
                mid_y = (waypoints[0][1] + waypoints[-1][1]) / 2 if len(waypoints) > 1 else waypoints[0][1]
            else:
                mid_x = (start_pt[0] + end_pt[0]) / 2
                mid_y = (start_pt[1] + end_pt[1]) / 2
            ax.text(mid_x, mid_y + label_offset_y, label, fontsize=8.5, fontweight="bold", color=color,
                    ha="center", va="center", bbox=dict(boxstyle="round,pad=0.25", fc="#ffffff", ec=color, lw=1.2), zorder=7)

        # Ký hiệu Card 1 và N
        ax.text(start_pt[0] + (12 if start_pt[0] < end_pt[0] else -12), start_pt[1] + 8, card_start,
                fontsize=9, fontweight="bold", color=color, zorder=7)
        ax.text(end_pt[0] - 16, end_pt[1] + 8, card_end,
                fontsize=9, fontweight="bold", color=color, zorder=7)

    # 1. Categories (1) ---> Subcategories (N)
    draw_connector((320, 880), (320, 770), label="1 : N", card_start="1", card_end="N", color="#0284c7", label_offset_y=0)

    # 2. Categories (1) ---> Articles (N) (qua category_id)
    draw_connector((510, 940), (670, 480), label="1 : N", card_start="1", card_end="N", color="#1d4ed8",
                   waypoints=[(600, 940), (600, 480)], label_offset_y=140)

    # 3. Subcategories (1) ---> Articles (N) (qua subcategory_id)
    draw_connector((510, 680), (670, 440), label="1 : N", card_start="1", card_end="N", color="#0891b2",
                   waypoints=[(620, 680), (620, 440)], label_offset_y=60)

    # 4. Authors (1) ---> Articles (N) (qua author_id)
    draw_connector((510, 360), (670, 610), label="1 : N", card_start="1", card_end="N", color="#059669",
                   waypoints=[(580, 360), (580, 610)], label_offset_y=-60)

    # 5. Articles (1) ---> ArticleFeatures (1 : 1) (qua article_id)
    draw_connector((1140, 875), (1280, 875), label="1 : 1 (Mở rộng 13 Đặc trưng)", card_start="1", card_end="1",
                   color="#7c3aed", label_offset_y=28)

    # Chú thích góc dưới (Legend)
    legend_y = 65
    ax.text(200, legend_y, "CHÚ THÍCH:", fontsize=10.5, fontweight="bold", color="#334155", va="center")
    ax.text(330, legend_y, "[PK] Khóa chính", fontsize=9.5, fontweight="bold", color="#b45309", va="center",
            bbox=dict(boxstyle="round,pad=0.25", fc="#fef3c7", ec="none"))
    ax.text(490, legend_y, "[FK] Khóa ngoại", fontsize=9.5, fontweight="bold", color="#0369a1", va="center",
            bbox=dict(boxstyle="round,pad=0.25", fc="#e0f2fe", ec="none"))
    ax.text(650, legend_y, "[UQ] Ràng buộc duy nhất", fontsize=9.5, fontweight="bold", color="#7e22ce", va="center",
            bbox=dict(boxstyle="round,pad=0.25", fc="#f3e8ff", ec="none"))
    ax.text(860, legend_y, "───► Quan hệ 1 : N / 1 : 1", fontsize=9.5, fontweight="bold", color="#1d4ed8", va="center")
    ax.text(1130, legend_y, "Chuẩn hóa 3NF: Tách biệt thực thể danh mục, tiểu mục, tác giả và bảng đặc trưng mô tả",
            fontsize=9.5, fontstyle="italic", color="#64748b", va="center")

    OUTPUT_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close()
    return OUTPUT_IMAGE


if __name__ == "__main__":
    out = draw_erd()
    print(f"Đã xuất sơ đồ ERD thành công: {out}")
