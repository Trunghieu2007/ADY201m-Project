import os
import re
import sys
import time
import json
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import requests
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==============================================================================
# BIẾN SỐ CẤU HÌNH (Được phép tùy chỉnh)
# ==============================================================================
CRAWL_DAYS = 7        # Số ngày cào tính từ thời điểm hiện tại ngược về quá khứ
REQUEST_DELAY = 0.5   # Thời gian nghỉ (giây) giữa các request để bảo vệ server

# ==============================================================================
# HẰNG SỐ HỆ THỐNG
# ==============================================================================
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

def refine_article(html, url, fallback_date=None):
    """Trích xuất thông tin bài viết từ HTML (mặc định tác giả 'VnExpress')."""
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    og = soup.find("meta", {"property": "og:type"})
    if (og and og.get("content", "").lower() != "article") or not soup.find("h1"):
        return None

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
    category = crumbs[0] if crumbs else "Khác"
    subcategory = crumbs[1] if len(crumbs) > 1 else "Không có"

    # Nội dung toàn văn (gán cố định author = 'VnExpress')
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
    }

def validate_article(art, cutoff_datetime):
    """Kiểm tra hợp lệ nội dung và đảm bảo bài nằm trong khoảng N ngày."""
    if not art:
        return False, "Không phải bài báo văn bản"
    if not art.get("title"):
        return False, "Thiếu tiêu đề"

    content = art.get("content", "")
    word_count = len(content.split())
    if word_count < 50:
        return False, f"Nội dung quá ngắn ({word_count} từ)"

    pub_str = art.get("published_at")
    if pub_str:
        try:
            pub_dt = datetime.strptime(pub_str, "%Y-%m-%d %H:%M:%S")
            if pub_dt < cutoff_datetime:
                return False, f"Ngoài phạm vi {CRAWL_DAYS} ngày ({pub_str})"
        except Exception:
            pass

    return True, "Hợp lệ"

def collect_urls_from_rss(cutoff_datetime):
    """Thu thập danh sách URL bài viết từ RSS feeds của 16 chuyên mục."""
    now = datetime.now()
    print(f"[*] Thu thập URL bài viết từ RSS ({cutoff_datetime:%d/%m/%Y} -> {now:%d/%m/%Y})...")
    urls = {}

    for cat in CATEGORIES:
        xml = fetch(f"https://vnexpress.net/rss/{cat}.rss")
        if not xml:
            continue
        try:
            soup = BeautifulSoup(xml, "xml")
            for item in soup.find_all("item"):
                link_tag = item.find("link")
                link = link_tag.text.strip() if link_tag else ""
                if not link.endswith(".html") or "/video/" in link:
                    continue

                pub_tag = item.find("pubDate")
                if pub_tag and pub_tag.text:
                    try:
                        dt = parsedate_to_datetime(pub_tag.text.strip()).astimezone().replace(tzinfo=None)
                        if dt >= cutoff_datetime:
                            urls[link.split("?")[0]] = (dt.timestamp(), dt.strftime("%Y-%m-%d %H:%M:%S"))
                    except Exception:
                        urls[link.split("?")[0]] = (0.0, None)
                else:
                    urls[link.split("?")[0]] = (0.0, None)
        except Exception as e:
            print(f"[!] Lỗi phân tích RSS chuyên mục {cat}: {e}")

    sorted_urls = sorted(urls.items(), key=lambda x: x[1][0], reverse=True)
    print(f"[+] Tìm thấy tổng cộng {len(sorted_urls)} bài viết hợp lệ trong 7 ngày từ RSS.")
    return sorted_urls

def main():
    """Hàm chính điều phối tiến trình cào đơn luồng và chỉ xuất dữ liệu ra JSON."""
    now = datetime.now()
    cutoff_datetime = now - timedelta(days=CRAWL_DAYS)

    print("=" * 65)
    print(" THU THẬP BÀI VIẾT VNEXPRESS (CUSTOM CRAWLER) ")
    print(f" Cấu hình: Cào {CRAWL_DAYS} ngày gần nhất | Delay = {REQUEST_DELAY}s (Đơn luồng)")
    print(f" Nguồn: 16 RSS chuyên mục chính thức | Định dạng xuất: Chỉ file JSON")
    print("=" * 65)

    start_time = time.time()
    links = collect_urls_from_rss(cutoff_datetime)
    print(f"[*] Bắt đầu tải và xử lý {len(links)} bài viết...")

    articles = []
    report = {}

    for idx, (url, date_info) in enumerate(links, 1):
        html = fetch(url)
        raw_article = refine_article(html, url, date_info[1])
        is_valid, reason = validate_article(raw_article, cutoff_datetime)
        report[reason] = report.get(reason, 0) + 1

        if is_valid:
            articles.append(raw_article)

        if idx % 50 == 0 or idx == len(links):
            print(f"  -> Tiến độ: {idx}/{len(links)} bài (Đã lưu hợp lệ: {len(articles)} bài)")

    # Lưu duy nhất ra file JSON
    out_json = os.path.join(os.path.dirname(__file__), "vnexpress_data.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(" KẾT QUẢ THU THẬP ")
    print("=" * 65)
    print(f"[+] Đã lưu thành công: {len(articles)} bài viết vào {os.path.basename(out_json)}")
    print(f"[+] Thời gian hoàn thành: {elapsed:.1f} giây ({elapsed / 60:.1f} phút)")

    print("\n[+] Thống kê kiểm duyệt nội dung:")
    for reason, count in sorted(report.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {reason:<40}: {count:4d}")
    print("=" * 65)

if __name__ == "__main__":
    main()
