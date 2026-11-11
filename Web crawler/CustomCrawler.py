"""
Module thu thập và làm sạch dữ liệu bài báo từ VnExpress (CustomCrawler).
Cấu hình thu thập: Cào theo khoảng thời gian N ngày tính từ thời điểm hiện tại ngược về quá khứ.
"""
import os
import re
import sys
import time
import json
import random
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import pandas as pd
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==============================================================================
# BIẾN SỐ CẤU HÌNH (Được phép tùy chỉnh theo yêu cầu)
# ==============================================================================
CRAWL_DAYS = 7        # Số ngày cào tính từ thời điểm hiện tại ngược về quá khứ (mặc định: đúng 1 tuần)
REQUEST_DELAY = 0.5   # Thời gian nghỉ cơ bản (giây) giữa các request để bảo vệ server, tránh bị chặn / 429

# ==============================================================================
# HẰNG SỐ HỆ THỐNG
# ==============================================================================
MAX_WORKERS = 3       # Giới hạn số luồng đồng thời ở mức an toàn (2-3 luồng) để không dồn request
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

# 16 chuyên mục chính thức của VnExpress
CATEGORIES = [
    "thoi-su", "the-gioi", "kinh-doanh", "bat-dong-san", "khoa-hoc-cong-nghe",
    "giai-tri", "the-thao", "phap-luat", "giao-duc", "suc-khoe", "doi-song",
    "du-lich", "oto-xe-may", "tam-su", "y-kien", "thu-gian"
]

# 1. FETCH
def fetch(url):
    """
    Gửi request HTTP GET có kiểm soát tốc độ (rate limiting) và cơ chế thử lại (retry)
    khi gặp mã lỗi 429 (Too Many Requests) hoặc gián đoạn mạng.
    """
    # Nghỉ ngẫu nhiên quanh REQUEST_DELAY để tránh tần số gửi cố định
    jitter = random.uniform(0.8, 1.2)
    time.sleep(REQUEST_DELAY * jitter)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if res.status_code == 429:
                wait_time = (attempt + 1) * 3
                print(f"[!] Gặp 429 Too Many Requests tại {url}. Tạm dừng {wait_time}s...")
                time.sleep(wait_time)
                continue
            res.raise_for_status()
            res.encoding = "utf-8"
            return res.text
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2)
    return ""

# 2. REFINE
def normalize_datetime(raw):
    """Chuẩn hóa chuỗi ngày giờ từ web về định dạng YYYY-MM-DD HH:MM:SS."""
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
    """Trích xuất các trường thông tin của bài viết từ mã nguồn HTML."""
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Bỏ qua trang media/video không phải bài viết dạng text
    og = soup.find("meta", {"property": "og:type"})
    if og and og.get("content", "").lower() != "article":
        return None
    if not soup.find("h1"):
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
        a.text.strip()
        for a in soup.select("ul.breadcrumb li a")
        if a.text.strip().lower() not in ["", "trang chủ"]
    ]
    category = crumbs[0] if crumbs else "Khác"
    subcategory = crumbs[1] if len(crumbs) > 1 else "Không có"

    # Nội dung và tác giả
    paragraphs = [
        p for p in soup.select(".fck_detail p.Normal, .fck_detail p, article p")
        if p.text.strip()
    ]
    author = "VnExpress"
    idx = len(paragraphs) - 1

    while idx >= 0 and (len(paragraphs) - 1 - idx) < 3:
        txt = paragraphs[idx].text.strip()
        strong = paragraphs[idx].find("strong")

        if txt.startswith(("*", "Ảnh:", "Video:")):
            paragraphs.pop(idx)
        elif strong and len(txt) < 50:
            author = strong.text.strip()
            paragraphs.pop(idx)
            break
        idx -= 1

    content = "\n".join(p.text.strip() for p in paragraphs)

    # ID bài viết
    meta_id = soup.find("meta", {"name": "tt_article_id"})
    if meta_id and meta_id.get("content"):
        aid = meta_id["content"]
    else:
        aid = url.split("?")[0].split("-")[-1].replace(".html", "")

    return {
        "article_id": aid,
        "title": title,
        "description": description,
        "content": content,
        "author": author,
        "published_at": published_at,
        "category": category,
        "subcategory": subcategory,
        "url": url,
    }

# 3. VALIDATE
def validate_article(art, cutoff_datetime):
    """
    Kiểm tra tính hợp lệ cơ bản của bài viết và đảm bảo bài nằm trong khoảng N ngày quy định.
    """
    if not art:
        return False, "Không phải bài báo văn bản"

    if not art.get("title"):
        return False, "Thiếu tiêu đề"

    content = art.get("content", "")
    word_count = len(content.split())
    if word_count < 50:
        return False, f"Nội dung quá ngắn ({word_count} từ)"

    # Lọc chặt chẽ theo mốc thời gian N ngày trở lại
    pub_str = art.get("published_at")
    if pub_str:
        try:
            pub_dt = datetime.strptime(pub_str, "%Y-%m-%d %H:%M:%S")
            if pub_dt < cutoff_datetime:
                return False, f"Ngoài phạm vi {CRAWL_DAYS} ngày ({pub_str})"
        except Exception:
            pass

    return True, "Hợp lệ"

# 4. ĐIỀU PHỐI VÀ THU THẬP LINK THEO KHOẢNG THỜI GIAN
def parse_pipeline(url, fallback_date, cutoff_datetime):
    """Luồng xử lý một bài viết: tải -> bóc tách -> kiểm tra thời gian và nội dung."""
    try:
        html = fetch(url)
        raw_article = refine_article(html, url, fallback_date)
        is_valid, reason = validate_article(raw_article, cutoff_datetime)

        if is_valid:
            return raw_article, "OK"
        return None, reason
    except Exception as e:
        return None, f"Lỗi: {e}"

def collect_urls_by_time_window(cutoff_datetime):
    """
    Thu thập danh sách URL bài viết từ RSS của 16 chuyên mục và duyệt phân trang
    đến khi chạm ngưỡng ngày hết hạn (cutoff_datetime).
    """
    now = datetime.now()
    print(f"[*] Thu thập liên kết xuất bản từ: {cutoff_datetime:%Y-%m-%d %H:%M:%S} đến {now:%Y-%m-%d %H:%M:%S}...")
    urls = {}

    # Bước A: Quét 16 RSS feed chính thức
    print("  -> Quét RSS feeds của 16 chuyên mục...")
    for cat in CATEGORIES:
        try:
            xml = fetch(f"https://vnexpress.net/rss/{cat}.rss")
            soup = BeautifulSoup(xml, "xml")
            for item in soup.find_all("item"):
                link_tag = item.find("link")
                link = link_tag.text.strip() if link_tag else ""
                if not link.endswith(".html") or "/video/" in link:
                    continue

                pub_tag = item.find("pubDate")
                if pub_tag and pub_tag.text:
                    try:
                        dt = parsedate_to_datetime(pub_tag.text.strip())
                        # Chuyển về giờ local naive
                        dt_naive = dt.astimezone().replace(tzinfo=None)
                        if dt_naive >= cutoff_datetime:
                            urls[link.split("?")[0]] = (dt_naive.timestamp(), dt_naive.strftime("%Y-%m-%d %H:%M:%S"))
                    except Exception:
                        urls[link.split("?")[0]] = (0.0, None)
                else:
                    urls[link.split("?")[0]] = (0.0, None)
        except Exception:
            pass

    print(f"  [+] Đã tìm thấy {len(urls)} bài hợp lệ từ RSS.")

    # Bước B: Quét thêm phân trang danh mục nếu cần lấy sâu đủ N ngày
    print(f"  -> Quét phân trang danh mục để gom đủ toàn bộ bài trong vòng {CRAWL_DAYS} ngày...")
    for cat in CATEGORIES:
        page = 1
        stop_cat = False
        while not stop_cat and page <= 15:
            try:
                page_url = f"https://vnexpress.net/{cat}" if page == 1 else f"https://vnexpress.net/{cat}-p{page}"
                html = fetch(page_url)
                soup = BeautifulSoup(html, "html.parser")
                articles_tags = soup.select("article.item-news h3.title-news a[href]")

                if not articles_tags:
                    break

                for a in articles_tags:
                    href = a["href"].split("?")[0]
                    if href.startswith("/"):
                        href = "https://vnexpress.net" + href
                    if href.endswith(".html") and "/video/" not in href and href not in urls:
                        urls[href] = (0.0, None)

            except Exception:
                break
            page += 1

    sorted_urls = sorted(urls.items(), key=lambda x: x[1][0], reverse=True)
    return sorted_urls

def main():
    """Hàm chính điều phối toàn bộ tiến trình thu thập bài báo theo khung thời gian."""
    now = datetime.now()
    cutoff_datetime = now - timedelta(days=CRAWL_DAYS)

    print("=" * 70)
    print(" THU THẬP BÀI VIẾT VNEXPRESS (CUSTOM CRAWLER) ")
    print(f" Khung thời gian: Đúng {CRAWL_DAYS} ngày gần nhất (tính từ lúc chạy)")
    print(f" Từ: {cutoff_datetime:%Y-%m-%d %H:%M:%S} -> Đến: {now:%Y-%m-%d %H:%M:%S}")
    print(f" Cấu hình an toàn: Delay = {REQUEST_DELAY}s | Luồng tối đa = {MAX_WORKERS}")
    print("=" * 70)

    start_time = time.time()
    links = collect_urls_by_time_window(cutoff_datetime)
    print(f"[*] Tổng số liên kết ứng viên cần xử lý: {len(links)} bài.")

    articles = []
    report = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(parse_pipeline, u, d[1], cutoff_datetime): u
            for u, d in links
        }
        for f in as_completed(futures):
            art, reason = f.result()
            report[reason] = report.get(reason, 0) + 1
            if art:
                articles.append(art)

    # Lọc lại lần cuối bảo đảm 100% bài thuộc đúng khung N ngày
    valid_articles = []
    for art in articles:
        pub_str = art.get("published_at")
        if pub_str:
            try:
                pub_dt = datetime.strptime(pub_str, "%Y-%m-%d %H:%M:%S")
                if pub_dt >= cutoff_datetime:
                    valid_articles.append(art)
                else:
                    report[f"Ngoài phạm vi {CRAWL_DAYS} ngày"] = report.get(f"Ngoài phạm vi {CRAWL_DAYS} ngày", 0) + 1
            except Exception:
                valid_articles.append(art)
        else:
            valid_articles.append(art)

    valid_articles.sort(key=lambda x: str(x.get("published_at", "")), reverse=True)
    df = pd.DataFrame(valid_articles)

    out_file = os.path.join(os.path.dirname(__file__), "vnexpress_data.csv")
    df.to_csv(out_file, index=False, encoding="utf-8-sig")

    out_json = os.path.join(os.path.dirname(__file__), "vnexpress_data.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(valid_articles, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(" KẾT QUẢ THU THẬP ")
    print("=" * 70)
    print(f"[+] Đã lưu: {len(df)} bài viết đạt tiêu chuẩn")
    print(f"[+] Tệp kết quả: {os.path.basename(out_file)} & {os.path.basename(out_json)}")
    print(f"[+] Thời gian hoàn thành: {elapsed:.1f} giây ({elapsed / 60:.1f} phút)")
    if not df.empty and "published_at" in df.columns:
        valid_dates = df["published_at"].dropna()
        if not valid_dates.empty:
            print(f"[+] Khoảng thời gian thực tế: từ {valid_dates.min()} đến {valid_dates.max()}")

    print("\n[+] Thống kê chi tiết quá trình kiểm duyệt nội dung:")
    for reason, count in sorted(report.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {reason:<45}: {count:4d}")
    print("=" * 70)

if __name__ == "__main__":
    main()
