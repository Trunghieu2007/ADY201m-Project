import os
import re
import sys
import time
import json
from datetime import datetime
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import pandas as pd
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- CẤU HÌNH ---
TARGET_ARTICLES = 500  # Số lượng bài viết cần lấy

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"
}

CATEGORIES = [
    "thoi-su", "the-gioi", "kinh-doanh", "bat-dong-san", "khoa-hoc-cong-nghe",
    "giai-tri", "the-thao", "phap-luat", "giao-duc", "suc-khoe", "doi-song",
    "du-lich", "oto-xe-may", "tam-su", "y-kien", "thu-gian"
]

# 1. FETCH
def fetch(url):
    """Gửi request HTTP GET để lấy nội dung HTML của URL."""
    res = requests.get(url, headers=HEADERS, timeout=12)
    res.raise_for_status()
    res.encoding = "utf-8"
    return res.text

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
def validate_article(art):
    """Kiểm tra tính hợp lệ cơ bản của bài viết."""
    if not art:
        return False, "Không phải bài báo văn bản"

    if not art.get("title"):
        return False, "Thiếu tiêu đề"

    content = art.get("content", "")
    word_count = len(content.split())
    if word_count < 50:
        return False, f"Nội dung quá ngắn ({word_count} từ)"

    return True, "Hợp lệ"

# 4. ĐIỀU PHỐI VÀ THU THẬP LINK
def parse_pipeline(url, fallback_date):
    """Luồng xử lý một bài viết: tải -> bóc tách -> kiểm tra."""
    try:
        time.sleep(0.02)
        html = fetch(url)
        raw_article = refine_article(html, url, fallback_date)
        is_valid, reason = validate_article(raw_article)

        if is_valid:
            return raw_article, "OK"
        return None, reason
    except Exception as e:
        return None, f"Lỗi: {e}"

def collect_urls(target_count):
    """Thu thập danh sách URL bài viết từ RSS và phân trang chuyên mục."""
    print(f"[*] Thu thập liên kết bài viết (Mục tiêu: {target_count} bài)...")
    urls = {}

    # Quét từ RSS
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
                try:
                    dt = parsedate_to_datetime(pub_tag.text.strip())
                    urls[link.split("?")[0]] = (dt.timestamp(), dt.strftime("%Y-%m-%d %H:%M:%S"))
                except Exception:
                    urls[link.split("?")[0]] = (0.0, None)
        except Exception:
            pass

    # Quét thêm từ trang chuyên mục nếu RSS chưa đủ
    page = 1
    while len(urls) < target_count and page <= 20:
        added = 0
        for cat in CATEGORIES:
            try:
                html = fetch(f"https://vnexpress.net/{cat}-p{page}")
                soup = BeautifulSoup(html, "html.parser")
                for a in soup.select("article.item-news h3.title-news a[href]"):
                    href = a["href"].split("?")[0]
                    if href.startswith("/"):
                        href = "https://vnexpress.net" + href
                    if href.endswith(".html") and "/video/" not in href and href not in urls:
                        urls[href] = (0.0, None)
                        added += 1
                        if len(urls) >= target_count:
                            break
            except Exception:
                pass

            if len(urls) >= target_count:
                break

        if added == 0 and page > 3:
            break
        page += 1

    sorted_urls = sorted(urls.items(), key=lambda x: x[1][0], reverse=True)
    return sorted_urls[:target_count]

def main():
    """Hàm chính điều phối toàn bộ tiến trình thu thập và xuất dữ liệu ra CSV."""
    print("=" * 65)
    print(" THU THẬP BÀI VIẾT VNEXPRESS ")
    print(f" Mục tiêu: {TARGET_ARTICLES} bài")
    print("=" * 65)

    start_time = time.time()
    links = collect_urls(TARGET_ARTICLES)
    print(f"[*] Bắt đầu tải và xử lý {len(links)} bài viết...")

    articles = []
    report = {}

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(parse_pipeline, u, d[1]): u
            for u, d in links
        }
        for f in as_completed(futures):
            art, reason = f.result()
            report[reason] = report.get(reason, 0) + 1
            if art:
                articles.append(art)
                if len(articles) >= TARGET_ARTICLES:
                    break

    articles.sort(key=lambda x: str(x.get("published_at", "")), reverse=True)
    df = pd.DataFrame(articles)

    out_file = os.path.join(os.path.dirname(__file__), "vnexpress_data.csv")
    df.to_csv(out_file, index=False, encoding="utf-8-sig")

    out_json = os.path.join(os.path.dirname(__file__), "vnexpress_data.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(" KẾT QUẢ ")
    print("=" * 65)
    print(f"[+] Đã lưu: {len(df)} bài")
    print(f"[+] Tệp kết quả: {os.path.basename(out_file)}")
    print(f"[+] Thời gian: {elapsed:.1f} giây")
    if not df.empty:
        print(f"[+] Khoảng thời gian: từ {df['published_at'].min()} đến {df['published_at'].max()}")

    print("\n[+] Thống kê kiểm tra nội dung:")
    for reason, count in report.items():
        print(f"  - {reason:<35}: {count:4d}")
    print("=" * 65)

if __name__ == "__main__":
    main()
