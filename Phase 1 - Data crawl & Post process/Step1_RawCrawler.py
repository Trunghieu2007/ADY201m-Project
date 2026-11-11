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

REQUEST_DELAY = 0.5
TIMEOUT = 12
CRAWL_DAYS = 7   # Phạm vi lấy bài: 7 ngày gần nhất tính từ thời điểm chạy

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
    time.sleep(REQUEST_DELAY)
    try:
        res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        res.raise_for_status()
        res.encoding = "utf-8"
        return res.text
    except requests.RequestException:
        return ""

def normalize_datetime(raw):
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
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    og = soup.find("meta", {"property": "og:type"})
    og_type = og.get("content", "").lower() if og else "unknown"

    date_tag = soup.find("span", class_="date")
    raw_date = date_tag.text.strip() if date_tag else ""
    if not raw_date:
        m_date = soup.find("meta", {"name": "pubdate"})
        raw_date = m_date.get("content", "").strip() if m_date else ""
    published_at = normalize_datetime(raw_date) or fallback_date

    h1 = soup.find("h1", class_="title-detail") or soup.find("h1")
    title = h1.text.strip() if h1 else ""

    desc_tag = soup.find("p", class_="description")
    description = desc_tag.text.strip() if desc_tag else ""
    if not description:
        m_desc = soup.find("meta", {"name": "description"}) or soup.find("meta", {"property": "og:description"})
        description = m_desc.get("content", "").strip() if m_desc else ""

    crumbs = [
        a.text.strip() for a in soup.select("ul.breadcrumb li a")
        if a.text.strip().lower() not in ["", "trang chủ"]
    ]
    category = crumbs[0] if crumbs else default_category
    subcategory = crumbs[1] if len(crumbs) > 1 else "Không có"

    paragraphs = [
        p.text.strip() for p in soup.select(".fck_detail p.Normal, .fck_detail p, article p")
        if p.text.strip()
    ]
    content = "\n".join(paragraphs)

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
    print("[*] Quét toàn bộ RSS feeds của 16 chuyên mục VnExpress...")
    cutoff_dt = datetime.now() - timedelta(days=CRAWL_DAYS)
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
                if not link or not link.endswith(".html"):
                    continue

                pub_tag = item.find("pubDate")
                pub_str = None
                is_within_days = True
                if pub_tag and pub_tag.text:
                    try:
                        dt = parsedate_to_datetime(pub_tag.text.strip()).astimezone().replace(tzinfo=None)
                        pub_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                        if dt < cutoff_dt:
                            is_within_days = False
                    except Exception:
                        pass

                if not is_within_days:
                    continue

                clean_url = link.split("?")[0]
                if clean_url not in urls:
                    urls[clean_url] = (pub_str, cat)
        except Exception:
            pass

    print(f"[+] Tổng số liên kết độc nhất tìm thấy: {len(urls)} links.")
    return urls

def main():
    links_dict = collect_all_rss_links()
    print("-> Đang cào dữ liệu...")

    raw_articles = []
    for url, (pub_date, cat) in links_dict.items():
        html = fetch(url)
        art = extract_raw_article(html, url, pub_date, cat)
        if art:
            raw_articles.append(art)

    with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(raw_articles, f, ensure_ascii=False, indent=2)

    print(f"-> Đã cào xong {len(raw_articles)} bài!")
    rel_raw = os.path.relpath(RAW_OUTPUT_PATH, PROJECT_DIR)
    print(f"[+] Đã lưu tại: {rel_raw}")

if __name__ == "__main__":
    main()
