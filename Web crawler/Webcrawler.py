import os
import sys
import time
import json
import requests
# pyrefly: ignore[missing-import]
from bs4 import BeautifulSoup  # type: ignore
# pyrefly: ignore[missing-import]
import pandas as pd  # type: ignore

# Đảm bảo in tiếng Việt không bị lỗi font trên Windows
sys.stdout.reconfigure(encoding="utf-8")

#Header giả lập trình duyệt gửi kèm trong các request HTTP
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

#Cào chi tiết 1 bài báo VnExpress và trích xuất 9 trường dữ liệu
def parse_article(url):
    res = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. Article ID
    meta_id = soup.find("meta", {"name": "tt_article_id"})
    article_id = meta_id["content"] if meta_id and meta_id.get("content") else url.split("-")[-1].replace(".html", "")

    # 2. Title
    h1 = soup.find("h1", class_="title-detail")
    title = h1.text.strip() if h1 else ""

    # 3. Description
    desc = soup.find("p", class_="description")
    description = desc.text.strip() if desc else ""

    # 4. Published Date
    date_tag = soup.find("span", class_="date")
    published_at = date_tag.text.strip() if date_tag else ""

    # 5 & 6. Category & Subcategory
    breadcrumbs = [a.text.strip() for a in soup.select("ul.breadcrumb li a")]
    category = breadcrumbs[0] if len(breadcrumbs) >= 1 else "Khác"
    subcategory = breadcrumbs[1] if len(breadcrumbs) >= 2 else "Không có"

    # 7 & 8. Content & Author
    paragraphs = soup.select(".fck_detail p.Normal")
    author = "VnExpress"
    content_lines = []

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
    rss_url = "https://vnexpress.net/rss/tin-moi-nhat.rss"
    print("Đang lấy danh sách tin từ RSS...")
    res = requests.get(rss_url, headers=HEADERS, timeout=10)
    
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
            data = parse_article(link)
            articles.append(data)
        except Exception as e:
            print(f"   Lỗi bài {link}: {e}")
        time.sleep(0.5)

    return articles

if __name__ == "__main__":
    #Khởi chạy cào dữ liệu RSS và lưu kết quả ra file JSON và CSV
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
