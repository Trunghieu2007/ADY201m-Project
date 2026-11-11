"""
BƯỚC 2: LÀM SẠCH & LỌC CHẤT LƯỢNG DỮ LIỆU (DATA FILTER)
Nhiệm vụ: Đọc tệp dữ liệu thô 'vnexpress_raw.json' (hoàn toàn không tốn mạng/request),
áp dụng các quy tắc kiểm duyệt chất lượng, xuất ra 'vnexpress_data.json' sạch
kèm báo cáo kiểm toán chi tiết (Audit Report) giải trình từng bài bị loại.
"""
import os
import sys
import json
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==============================================================================
# QUY TẮC NGHIỆP VỤ LỌC DỮ LIỆU (Tùy chỉnh linh hoạt mà không cần cào lại mạng)
# ==============================================================================
FILTER_DAYS = 7             # Số ngày tối đa tính từ thời điểm chạy ngược về trước
MIN_WORD_COUNT = 50         # Số lượng từ tối thiểu của bài viết dạng văn bản chuẩn
REQUIRE_TITLE = True        # Bắt buộc bài viết phải có tiêu đề
EXCLUDE_NON_ARTICLE = True  # Loại bỏ trang video, clip, media, podcast (og:type != 'article')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

# Hỗ trợ tìm file thô ở Data pipeline hoặc Web crawler
RAW_CANDIDATES = [
    os.path.join(BASE_DIR, "vnexpress_raw.json"),
    os.path.join(PROJECT_DIR, "Web crawler", "vnexpress_raw.json"),
    os.path.join(PROJECT_DIR, "Web crawler", "vnexpress_data.json"),
]

FILTERED_OUTPUT_PATHS = [
    os.path.join(BASE_DIR, "vnexpress_data.json"),
    os.path.join(PROJECT_DIR, "Web crawler", "vnexpress_data.json"),
]

AUDIT_LOG_PATH = os.path.join(BASE_DIR, "audit_rejection_report.json")

def load_raw_dataset():
    """Tải tập dữ liệu thô từ đĩa cứng."""
    for path in RAW_CANDIDATES:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[*] Nạp thành công {len(data)} bài viết thô từ: {os.path.relpath(path, PROJECT_DIR)}")
            return data, path
    raise FileNotFoundError(
        f"[!] Chưa tìm thấy tệp dữ liệu thô 'vnexpress_raw.json'. Hãy chạy Step1_RawCrawler.py trước."
    )

def audit_and_filter(raw_articles):
    """
    Áp dụng toàn bộ quy tắc kiểm toán chất lượng lên từng bài viết thô.
    Trả về: danh sách bài hợp lệ, danh sách bài bị loại kèm lý do, thống kê tóm tắt.
    """
    now = datetime.now()
    cutoff_datetime = now - timedelta(days=FILTER_DAYS)

    valid_articles = []
    rejected_records = []
    reason_stats = {}

    for art in raw_articles:
        aid = art.get("article_id", "N/A")
        url = art.get("url", "")
        title = art.get("title", "").strip()
        content = art.get("content", "").strip()
        pub_str = art.get("published_at")
        og_type = art.get("og_type", "article")

        # 1. Kiểm tra tiêu đề
        if REQUIRE_TITLE and not title:
            reason = "Thiếu tiêu đề (Empty title)"
            reason_stats[reason] = reason_stats.get(reason, 0) + 1
            rejected_records.append({"article_id": aid, "url": url, "reason": reason})
            continue

        # 2. Kiểm tra định dạng bài viết text
        if EXCLUDE_NON_ARTICLE and og_type not in ["article", "unknown", ""]:
            reason = f"Không phải bài báo văn bản (og:type = {og_type})"
            reason_stats[reason] = reason_stats.get(reason, 0) + 1
            rejected_records.append({"article_id": aid, "url": url, "reason": reason})
            continue

        # 3. Kiểm tra độ dài nội dung
        words = len(content.split())
        if words < MIN_WORD_COUNT:
            reason = f"Nội dung quá ngắn ({words} từ < ngưỡng {MIN_WORD_COUNT} từ)"
            reason_stats[reason] = reason_stats.get(reason, 0) + 1
            rejected_records.append({"article_id": aid, "url": url, "reason": reason, "word_count": words})
            continue

        # 4. Kiểm tra khung thời gian N ngày
        if pub_str:
            try:
                pub_dt = datetime.strptime(pub_str, "%Y-%m-%d %H:%M:%S")
                if pub_dt < cutoff_datetime:
                    reason = f"Ngoài phạm vi {FILTER_DAYS} ngày gần nhất ({pub_str})"
                    reason_stats[reason] = reason_stats.get(reason, 0) + 1
                    rejected_records.append({"article_id": aid, "url": url, "reason": reason, "published_at": pub_str})
                    continue
            except Exception:
                pass

        # Chuẩn hóa lại cấu trúc chuẩn mực cho các bước tiếp theo
        clean_article = {
            "article_id": aid,
            "title": title,
            "description": art.get("description", "").strip(),
            "content": content,
            "author": art.get("author", "VnExpress"),
            "published_at": pub_str,
            "category": art.get("category", "Khác"),
            "subcategory": art.get("subcategory", "Không có"),
            "url": url,
        }
        valid_articles.append(clean_article)

    # Sắp xếp bài mới nhất lên đầu
    valid_articles.sort(key=lambda x: str(x.get("published_at", "")), reverse=True)

    summary = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "filter_days": FILTER_DAYS,
        "min_word_count": MIN_WORD_COUNT,
        "cutoff_datetime": cutoff_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "total_raw": len(raw_articles),
        "total_valid": len(valid_articles),
        "total_rejected": len(rejected_records),
        "retention_rate_pct": round(len(valid_articles) / len(raw_articles) * 100, 2) if raw_articles else 0,
        "reason_breakdown": reason_stats,
        "rejected_articles_detail": rejected_records
    }

    return valid_articles, summary

def main():
    """Điều phối toàn bộ quá trình đọc thô, kiểm duyệt và lưu trữ dữ liệu sạch."""
    print("=" * 65)
    print(" BƯỚC 2: LÀM SẠCH & LỌC CHẤT LƯỢNG DỮ LIỆU (DATA FILTER) ")
    print(f" Tiêu chí: Đúng {FILTER_DAYS} ngày gần nhất | Độ dài tối thiểu >= {MIN_WORD_COUNT} từ")
    print("=" * 65)

    raw_data, raw_path = load_raw_dataset()
    valid_articles, summary = audit_and_filter(raw_data)

    # Lưu dữ liệu sạch ra cả thư mục Data pipeline và đồng bộ sang Web crawler
    for out_path in FILTERED_OUTPUT_PATHS:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(valid_articles, f, ensure_ascii=False, indent=2)

    # Lưu báo cáo kiểm toán
    with open(AUDIT_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 65)
    print(" KẾT QUẢ KIỂM TOÁN VÀ LỌC DỮ LIỆU ")
    print("=" * 65)
    print(f"[+] Tổng số bài đầu vào thô:  {summary['total_raw']:4d} bài (100.0%)")
    print(f"[+] Số bài đạt chuẩn giữ lại: {summary['total_valid']:4d} bài ({summary['retention_rate_pct']}%)")
    print(f"[+] Số bài bị loại bỏ:        {summary['total_rejected']:4d} bài ({100 - summary['retention_rate_pct']:.2f}%)")
    print(f"[+] Đã xuất dữ liệu sạch sang: vnexpress_data.json")
    print(f"[+] Đã lưu báo cáo kiểm toán: {os.path.basename(AUDIT_LOG_PATH)}")

    print("\n[+] Chi tiết nguyên nhân loại bỏ bài viết:")
    for reason, count in sorted(summary["reason_breakdown"].items(), key=lambda x: x[1], reverse=True):
        pct = (count / summary["total_raw"]) * 100
        print(f"  - {reason:<45}: {count:3d} bài ({pct:4.1f}%)")
    print("=" * 65)

if __name__ == "__main__":
    main()
