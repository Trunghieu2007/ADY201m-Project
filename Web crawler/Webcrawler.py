import os
import re
import sys
import time
import json
from datetime import datetime
# pyrefly: ignore[missing-import]
import requests  # type: ignore
# pyrefly: ignore[missing-import]
from bs4 import BeautifulSoup  # type: ignore
# pyrefly: ignore[missing-import]
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

# Gửi request kèm kiểm tra lỗi HTTP và ép mã hóa UTF-8
def fetch(url):
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()          # ném exception nếu 4xx/5xx -> tránh nạp trang rác
    res.encoding = "utf-8"          # VnExpress dùng UTF-8, tránh đoán sai mã hóa
    return res

# Đọc robots.txt và trả về danh sách đường dẫn bị cấm (áp dụng cho User-agent *)
def load_disallow():
    disallow = []
    try:
        text = fetch(f"{BASE_URL}/robots.txt").text
        applies = False
        for line in text.splitlines():
            line = line.strip()
            if line.lower().startswith("user-agent:"):
                applies = line.split(":", 1)[1].strip() == "*"
            elif applies and line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path and path != "/":
                    disallow.append(BASE_URL + path)
    except Exception as e:
        print(f"[!] Không đọc được robots.txt ({e}), bỏ qua kiểm tra cho phép.")
    return disallow

#URL có được phép cào theo robots.txt không
def is_allowed(url, disallow):
    return not any(url.startswith(p) for p in disallow)

#Ép thời gian tiếng Việt về định dạng DATETIME 'YYYY-MM-DD HH:MM:SS'
def normalize_datetime(raw):
    if not raw:
        return None
    m = re.search(r"\d{1,2}/\d{1,2}/\d{4}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?", raw)
    if not m:
        return None
    s = m.group(0).strip()
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return None

#Bóc các đoạn văn nội dung, thử nhiều selector dự phòng nếu markup VnExpress thay đổi
def extract_paragraphs(soup):
    for sel in (".fck_detail p.Normal", ".fck_detail p", "#main-content p.Normal", ".article-detail p.Normal"):
        paragraphs = soup.select(sel)
        if paragraphs:
            return paragraphs
    return []

#Cào chi tiết 1 bài báo VnExpress và trích xuất 9 trường dữ liệu
def parse_article(url):
    soup = BeautifulSoup(fetch(url).text, "html.parser")

    # 1. Article ID
    meta_id = soup.find("meta", {"name": "tt_article_id"})
    article_id = meta_id["content"] if meta_id and meta_id.get("content") else url.split("-")[-1].replace(".html", "")

    # 2. Title
    h1 = soup.find("h1", class_="title-detail")
    title = h1.text.strip() if h1 else ""

    # 3. Description
    desc = soup.find("p", class_="description")
    description = desc.text.strip() if desc else ""

    # 4. Published Date (ép về DATETIME)
    date_tag = soup.find("span", class_="date")
    published_at = normalize_datetime(date_tag.text.strip() if date_tag else "")

    # 5 & 6. Category & Subcategory
    breadcrumbs = [a.text.strip() for a in soup.select("ul.breadcrumb li a")]
    category = breadcrumbs[0] if len(breadcrumbs) >= 1 else "Khác"
    subcategory = breadcrumbs[1] if len(breadcrumbs) >= 2 else "Không có"

    # 7 & 8. Content & Author
    paragraphs = extract_paragraphs(soup)
    author = "VnExpress"

    if paragraphs:
        last_p = paragraphs[-1]
        strong_tag = last_p.find("strong")
        if strong_tag and len(last_p.text.strip()) < 50:
            author = strong_tag.text.strip()
            paragraphs = paragraphs[:-1]

    content_lines = [p.text.strip() for p in paragraphs if p.text.strip()]
    content = "\n".join(content_lines)

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

#Thu thập danh sách URL từ RSS tin mới nhất VnExpress và cào nội dung từng bài
def crawl_rss():
    print("Đang lấy danh sách tin từ RSS...")
    res = fetch(RSS_URL)
    soup = BeautifulSoup(res.content, "xml")
    disallow = load_disallow()
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
        if not is_allowed(link, disallow):
            print(f"-> Bỏ qua (robots.txt): {link}")
            continue

        print(f"-> Đang cào: {link}")
        try:
            articles.append(parse_article(link))
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
