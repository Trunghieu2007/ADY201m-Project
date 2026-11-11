import os
import sys
import json
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FILTER_DAYS = 7
MIN_WORD_COUNT = 50

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

RAW_CANDIDATES = [
    os.path.join(BASE_DIR, "vnexpress_raw.json"),
    os.path.join(PROJECT_DIR, "Web crawler", "vnexpress_raw.json"),
    os.path.join(PROJECT_DIR, "Web crawler", "vnexpress_data.json"),
]

FILTERED_OUTPUT_PATHS = [
    os.path.join(BASE_DIR, "vnexpress_data.json"),
    os.path.join(PROJECT_DIR, "Web crawler", "vnexpress_data.json"),
]

def load_raw_dataset():
    for path in RAW_CANDIDATES:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError("Chưa tìm thấy tệp dữ liệu thô 'vnexpress_raw.json'. Hãy chạy Step1_RawCrawler.py trước.")

def filter_articles(raw_articles):
    cutoff_datetime = datetime.now() - timedelta(days=FILTER_DAYS)
    valid_articles = []

    for art in raw_articles:
        title = art.get("title", "").strip()
        content = art.get("content", "").strip()
        pub_str = art.get("published_at")
        og_type = art.get("og_type", "article")

        if not title:
            continue
        if og_type not in ["article", "unknown", ""]:
            continue
        if len(content.split()) < MIN_WORD_COUNT:
            continue

        if pub_str:
            try:
                if datetime.strptime(pub_str, "%Y-%m-%d %H:%M:%S") < cutoff_datetime:
                    continue
            except Exception:
                pass

        valid_articles.append({
            "article_id": art.get("article_id", "N/A"),
            "title": title,
            "description": art.get("description", "").strip(),
            "content": content,
            "author": "VnExpress",
            "published_at": pub_str,
            "category": art.get("category", "Khác"),
            "subcategory": art.get("subcategory", "Không có"),
            "url": art.get("url", ""),
        })

    valid_articles.sort(key=lambda x: str(x.get("published_at", "")), reverse=True)
    return valid_articles

def main():
    raw_data = load_raw_dataset()
    valid_articles = filter_articles(raw_data)

    for out_path in FILTERED_OUTPUT_PATHS:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(valid_articles, f, ensure_ascii=False, indent=2)

    rejected_count = len(raw_data) - len(valid_articles)
    print(f"[+] Tổng số bài đầu vào thô:  {len(raw_data)} bài")
    print(f"[+] Số bài đạt chuẩn giữ lại: {len(valid_articles)} bài")
    print(f"[+] Số bài bị loại bỏ:        {rejected_count} bài")
    print("[+] Đã xuất dữ liệu sạch sang: vnexpress_data.json")

if __name__ == "__main__":
    main()
