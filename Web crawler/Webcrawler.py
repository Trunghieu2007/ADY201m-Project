import os
import re
import sys
import time
import json
from datetime import datetime
import requests  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
import pandas as pd  # type: ignore

# Đảm bảo in tiếng Việt không bị lỗi font trên Windows
sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://vnexpress.net"
RSS_URL = f"{BASE_URL}/rss/tin-moi-nhat.rss"
CRAWL_DELAY = 1.0  # giây nghỉ giữa các request để lịch sự với server

# Header giả lập trình duyệt gửi kèm trong các request HTTP
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

#fetch: gửi request HTTP, kiểm tra lỗi 4xx/5xx và ép mã hóa UTF-8
def fetch(url):
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()          # ném exception nếu 4xx/5xx -> tránh nạp trang rác
    res.encoding = "utf-8"          # VnExpress dùng UTF-8, tránh đoán sai mã hóa
    return res

#normalize_datetime: ép ngày giờ (dd/mm/yyyy HH:MM hoặc ISO) về 'YYYY-MM-DD HH:MM:SS'
def normalize_datetime(raw):
    if not raw:
        return None
    iso = re.search(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}", raw)   # dạng 2026-10-24T18:00 (meta pubdate)
    if iso:
        return datetime.strptime(iso.group(0).replace("T", " "), "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
    dm = re.search(r"\d{1,2}/\d{1,2}/\d{4}", raw)          # ngày: 17/10/2026
    if not dm:
        return None
    dt = datetime.strptime(dm.group(0), "%d/%m/%Y")
    tm = re.search(r"\d{1,2}:\d{2}", raw)                   # giờ: 23:37 (bỏ qua dấu phẩy/GMT)
    if tm:
        h, m = map(int, tm.group(0).split(":"))
        dt = dt.replace(hour=h, minute=m)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

#is_article_page: loại trang video/clip/album (og:type khác "article" hoặc không có thẻ h1)
def is_article_page(soup):
    og = soup.find("meta", {"property": "og:type"})
    og_type = og.get("content", "").strip().lower() if og else ""
    if og_type and og_type != "article":
        return False
    return soup.find("h1") is not None

#extract_paragraphs: bóc đoạn văn có chữ, ưu tiên selector cho >=2 đoạn (selector hẹp
#có thể chỉ bắt được dòng byline); trả về danh sách đoạn dự phòng nếu không selector nào đủ
def extract_paragraphs(soup):
    fallback = []
    for sel in (".fck_detail p.Normal", ".fck_detail p", "#main-content p.Normal",
                ".article-detail p.Normal", "article p"):
        paragraphs = [p for p in soup.select(sel) if p.text.strip()]
        if len(paragraphs) >= 2:
            return paragraphs
        if paragraphs and not fallback:
            fallback = paragraphs
    return fallback

#parse_article: cào 1 bài và trả về dict 9 trường; trả về None nếu không phải bài báo hợp lệ
def parse_article(url):
    soup = BeautifulSoup(fetch(url).text, "html.parser")

    # 0. Bỏ trang video/clip vì không có nội dung bài báo để phân tích
    if not is_article_page(soup):
        print(f"   Bỏ qua (không phải bài báo): {url}")
        return None

    # 1. Article ID
    meta_id = soup.find("meta", {"name": "tt_article_id"})
    article_id = meta_id["content"] if meta_id and meta_id.get("content") else url.split("-")[-1].replace(".html", "")

    # 2. Title: ưu tiên h1.title-detail, dự phòng h1 bất kỳ
    h1 = soup.find("h1", class_="title-detail") or soup.find("h1")
    title = h1.text.strip() if h1 else ""

    # 3. Description
    desc = soup.find("p", class_="description")
    description = desc.text.strip() if desc else ""

    # 4. Published Date: span.date, dự phòng meta pubdate (dạng ISO)
    date_tag = soup.find("span", class_="date")
    raw_date = date_tag.text.strip() if date_tag else ""
    if not raw_date:
        meta_date = soup.find("meta", {"name": "pubdate"})
        raw_date = meta_date["content"] if meta_date and meta_date.get("content") else ""
    published_at = normalize_datetime(raw_date)

    # 5 & 6. Category & Subcategory (breadcrumb đầu là icon home, lấy title khi không có chữ)
    breadcrumbs = [(a.text.strip() or a.get("title", "").strip())
                   for a in soup.select("ul.breadcrumb li a")]
    breadcrumbs = [b for b in breadcrumbs if b]
    category = breadcrumbs[0] if len(breadcrumbs) >= 1 else "Khác"
    subcategory = breadcrumbs[1] if len(breadcrumbs) >= 2 else "Không có"

    # 7 & 8. Content & Author (extract_paragraphs đã bỏ các đoạn rỗng)
    paragraphs = extract_paragraphs(soup)

    # Tên tác giả nằm ở đoạn cuối (in đậm, ngắn); strong rỗng thì giữ mặc định
    author = "VnExpress"
    if paragraphs:
        last_p = paragraphs[-1]
        strong_tag = last_p.find("strong")
        if strong_tag and len(last_p.text.strip()) < 50 and strong_tag.text.strip():
            author = strong_tag.text.strip()
            paragraphs = paragraphs[:-1]

    content_lines = [p.text.strip() for p in paragraphs if p.text.strip()]
    content = "\n".join(content_lines)

    # 9. Quality gate: bỏ bài thiếu tiêu đề hoặc thiếu nội dung
    if not title or not content:
        print(f"   Bỏ qua (thiếu title hoặc content): {url}")
        return None

    return {
        "article_id": article_id,
        "title": title,
        "description": description,
        "content": content,
        "author": author,
        "published_at": published_at,
        "category": category,
        "subcategory": subcategory,
        "url": url,
    }

#crawl_rss: đọc RSS tin mới nhất, cào từng bài hợp lệ và trả về danh sách bài báo
def crawl_rss():
    print("Đang lấy danh sách tin từ RSS...")
    res = fetch(RSS_URL)
    soup = BeautifulSoup(res.content, "xml")
    articles = []

    for item in soup.find_all("item"):
        link_tag = item.find("link")
        link = ""
        if link_tag:
            link = link_tag.text.strip() or (link_tag.next_sibling.strip() if link_tag.next_sibling else "")
        if not link and item.find("guid"):
            link = item.find("guid").text.strip()

        if not link.endswith(".html"):
            continue

        print(f"-> Đang cào: {link}")
        try:
            article = parse_article(link)
            if article:
                articles.append(article)
        except Exception as e:
            print(f"   Lỗi bài {link}: {e}")
        time.sleep(CRAWL_DELAY)

    return articles

if __name__ == "__main__":
    # Khởi chạy cào dữ liệu RSS và lưu kết quả ra file JSON và CSV
    data = crawl_rss()

    save_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(save_dir, "vnexpress_data.json")
    csv_path = os.path.join(save_dir, "vnexpress_data.csv")

    # 1. Lưu ra JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # 2. Lưu ra CSV cho bước Data Science (Pandas)
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"\nHoàn tất! Đã lưu {len(data)} bài báo vào 'vnexpress_data.json' và 'vnexpress_data.csv'.")
