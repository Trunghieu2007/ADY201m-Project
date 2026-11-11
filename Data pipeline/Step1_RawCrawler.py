"""
BƯỚC 1: CÀO DỮ LIỆU THÔ (RAW CRAWLER)
Nhiệm vụ: Quét toàn bộ RSS của 16 chuyên mục VnExpress, tải bài viết nguyên bản
và lưu trữ 100% không loại bỏ bài nào vào tệp 'vnexpress_raw.json'.
"""
import os
import re
import sys
import time
import json
from datetime import datetime
from email.utils import parsedate_to_datetime
import requests
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Cấu hình
REQUEST_DELAY = 0.5   # Thời gian nghỉ (giây) giữa các request
TIMEOUT = 12

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
}

CATEGORIES = [
    "thoi-su", "the-gioi", "kinh-doanh", "bat-dong-san", "khoa-hoc-cong-nghe",
    "giai-tri", "the-thao", "phap-luat", "giao-duc", "suc-khoe", "doi-song",
    "du-lich", "oto-xe-may", "tam-su", "y-kien", "thu-gian"
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
RAW_OUTPUT_PATH = os.path.join(BASE_DIR, "vnexpress_raw.json")

def fetch(url):
    """Gửi HTTP GET đơn luồng có thời gian nghỉ cố định REQUEST_DELAY."""
    time.sleep(REQUEST_DELAY)
    try:
        res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        res.raise_for_status()
        res.encoding = "utf-8"
        return res.text
    except requests.RequestException as e:
        print(f"[!] Lỗi fetch {url}: {e}")
        return ""

def normalize_datetime(raw):
    """Chuẩn hóa chuỗi ngày giờ từ web về YYYY-MM-DD HH:MM:SS."""
    if not raw:
        return None
    iso = re.search(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}", raw)
    if iso:
        return datetime.strptime(iso.group(0).replace("T", " "), "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")

    dm = re.search(r"\d{1,2}/\d{1,2}/\d{4}", raw)
    tm = re.search(r"\d{1,2}:\d{2}", raw)
    if dm:
        dt = datetime.strptime(dm.group(0), "%d/%m/%Y")
        if tm:
            h, m = map(int, tm.group(0).split(":"))
            dt = dt.replace(hour=h, minute=m)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return None

def extract_raw_article(html, url, fallback_date=None, default_category="Khác"):
    """Trích xuất toàn bộ dữ liệu bài viết nguyên bản từ HTML, không loại bỏ bất kỳ bài nào."""
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Kiểm tra og:type
    og = soup.find("meta", {"property": "og:type"})
    og_type = og.get("content", "").lower() if og else "unknown"

    # Thời gian xuất bản
    date_tag = soup.find("span", class_="date")
    raw_date = date_tag.text.strip() if date_tag else ""
    if not raw_date:
        m_date = soup.find("meta", {"name": "pubdate"})
        raw_date = m_date.get("content", "").strip() if m_date else ""
    published_at = normalize_datetime(raw_date) or fallback_date

    # Tiêu đề
    h1 = soup.find("h1", class_="title-detail") or soup.find("h1")
    title = h1.text.strip() if h1 else ""

    # Tóm tắt
    desc_tag = soup.find("p", class_="description")
    description = desc_tag.text.strip() if desc_tag else ""
    if not description:
        m_desc = soup.find("meta", {"name": "description"}) or soup.find("meta", {"property": "og:description"})
        description = m_desc.get("content", "").strip() if m_desc else ""

    # Chuyên mục
    crumbs = [
        a.text.strip() for a in soup.select("ul.breadcrumb li a")
        if a.text.strip().lower() not in ["", "trang chủ"]
    ]
    category = crumbs[0] if crumbs else default_category
    subcategory = crumbs[1] if len(crumbs) > 1 else "Không có"

    # Nội dung toàn văn nguyên bản
    paragraphs = [
        p.text.strip() for p in soup.select(".fck_detail p.Normal, .fck_detail p, article p")
        if p.text.strip()
    ]
    content = "\n".join(paragraphs)

    # ID bài viết
    meta_id = soup.find("meta", {"name": "tt_article_id"})
    aid = meta_id["content"] if meta_id and meta_id.get("content") else url.split("?")[0].split("-")[-1].replace(".html", "")

    return {
        "article_id": aid,
        "title": title,
        "description": description,
        "content": content,
        "author": "VnExpress",
        "published_at": published_at,
        "category": category,
        "subcategory": subcategory,
        "url": url,
        "og_type": og_type,
        "raw_word_count": len(content.split()),
        "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def collect_all_rss_links():
    """Thu thập 100% danh sách URL bài viết từ RSS feeds của 16 chuyên mục."""
    print("[*] Quét toàn bộ RSS feeds của 16 chuyên mục VnExpress...")
    urls = {}

    for cat in CATEGORIES:
        xml = fetch(f"https://vnexpress.net/rss/{cat}.rss")
        if not xml:
            continue
        try:
            soup = BeautifulSoup(xml, "xml")
            items = soup.find_all("item")
            cat_count = 0
            for item in items:
                link_tag = item.find("link")
                link = link_tag.text.strip() if link_tag else ""
                if not link or not link.endswith(".html"):
                    continue

                pub_tag = item.find("pubDate")
                pub_str = None
                if pub_tag and pub_tag.text:
                    try:
                        dt = parsedate_to_datetime(pub_tag.text.strip()).astimezone().replace(tzinfo=None)
                        pub_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass

                clean_url = link.split("?")[0]
                if clean_url not in urls:
                    urls[clean_url] = (pub_str, cat)
                    cat_count += 1
            print(f"  -> {cat:<20}: {cat_count:2d} links")
        except Exception as e:
            print(f"[!] Lỗi phân tích RSS chuyên mục {cat}: {e}")

    print(f"[+] Tổng số liên kết độc nhất tìm thấy: {len(urls)} links.")
    return urls

def main():
    """Chạy quy trình cào dữ liệu thô và lưu nguyên trạng vào vnexpress_raw.json."""
    print("=" * 65)
    print(" BƯỚC 1: CÀO DỮ LIỆU THÔ VNEXPRESS (RAW CRAWLER) ")
    print(" Cơ chế: Tải nguyên bản 100% links - Tuyệt đối không lọc bỏ ")
    print("=" * 65)

    start_time = time.time()
    links_dict = collect_all_rss_links()

    raw_articles = []
    total = len(links_dict)

    for idx, (url, (pub_date, cat)) in enumerate(links_dict.items(), 1):
        html = fetch(url)
        art = extract_raw_article(html, url, pub_date, cat)
        if art:
            raw_articles.append(art)

        if idx % 50 == 0 or idx == total:
            print(f"  -> Đã cào thô: {idx}/{total} bài ({len(raw_articles)} bài thành công)")

    with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(raw_articles, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(" HOÀN TẤT BƯỚC 1: CÀO DỮ LIỆU THÔ ")
    print("=" * 65)
    print(f"[+] Đã lưu trọn vẹn: {len(raw_articles)}/{total} bài vào {os.path.basename(RAW_OUTPUT_PATH)}")
    print(f"[+] Thời gian: {elapsed:.1f} giây ({elapsed / 60:.1f} phút)")
    print(f"[+] Vị trí file thô: {RAW_OUTPUT_PATH}")
    print("=" * 65)

if __name__ == "__main__":
    main()
