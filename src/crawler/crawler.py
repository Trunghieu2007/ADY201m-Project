"""Module thu thập (Crawler) dữ liệu bài báo tự động từ VnExpress.
Hỗ trợ khám phá tin tức qua RSS Feeds và Sitemap XML, bóc tách cấu trúc HTML5
thành từ điển 12 trường dữ liệu thô tuân thủ nguyên lý Ingestion trong Knowledge.md.
"""
from __future__ import annotations

import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

from src.utils import (
    CRAWL_LOG_PATH,
    PROJECT_ROOT,
    RAW_DATA_PATH,
    TARGET_CATEGORIES,
)

logger = logging.getLogger(__name__)

# Các thông số và đường dẫn cấu hình
RAW_DATA_DIR = RAW_DATA_PATH.parent
ARTICLE_OUTPUT = RAW_DATA_PATH
CRAWL_LOG_OUTPUT = CRAWL_LOG_PATH

BASE_URL = "https://vnexpress.net"
SITEMAP_URLS = (
    "https://vnexpress.net/google-news-sitemap.xml",
    "https://vnexpress.net/images-2026-sitemap.xml",
)
RSS_FEEDS = {
    "thoi-su": ("Thời sự", "https://vnexpress.net/rss/thoi-su.rss"),
    "kinh-doanh": ("Kinh doanh", "https://vnexpress.net/rss/kinh-doanh.rss"),
    "bat-dong-san": ("Bất động sản", "https://vnexpress.net/rss/bat-dong-san.rss"),
    "khoa-hoc-cong-nghe": ("Khoa học công nghệ", "https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss"),
    "suc-khoe": ("Sức khỏe", "https://vnexpress.net/rss/suc-khoe.rss"),
}
CATEGORIES = {k: v[0] for k, v in RSS_FEEDS.items()}

REQUEST_TIMEOUT, REQUEST_DELAY, MAX_ARTICLES = 20, 1.0, 20
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154.0.0.0 VnExpressDataScienceCrawler/0.1"
CREDIT_REGEX = re.compile(
    r"\s+(?:nhóm\s+thiết\s+kế|kết\s+cấu|đơn\s+vị\s+thi\s+công|ảnh|photo|photos|thiết\s+kế|\"?biên\s+tập\"?|biên\s+dịch)\s*:",
    re.I,
)
CATEGORY_PATHS = {
    "/thoi-su/": "Thời sự",
    "/kinh-doanh/": "Kinh doanh",
    "/bat-dong-san/": "Bất động sản",
    "/suc-khoe/": "Sức khỏe",
    "/khoa-hoc-cong-nghe/": "Khoa học công nghệ",
}


def fetch_url(url: str, retries: int = 3, delay: float = 1.0) -> str:
    """Tải nội dung HTML/XML với cơ chế thử lại (exponential retry) và giả lập trình duyệt.
    Tránh tình trạng bị chặn IP hoặc lỗi kết nối mạng tạm thời.
    """
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8"}
    for attempt in range(1, retries + 1):
        try:
            res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            res.raise_for_status()
            return res.text
        except requests.RequestException as exc:
            if attempt == retries:
                logger.error("Hết số lần thử (%d/%d) tải %s: %s", attempt, retries, url, exc)
                raise
            logger.warning("Thử lại (%d/%d) tải %s do lỗi: %s. Chờ %.1fs...", attempt, retries, url, exc, delay * attempt)
            time.sleep(delay * attempt)
    return ""


def clean_author(text: str | None) -> str | None:
    """Chuẩn hóa chuỗi tên tác giả, loại bỏ tiền tố ('Tác giả:', 'Theo') và thông tin hậu kỳ."""
    if not text:
        return None
    text = re.sub(r"^(tác giả|tac gia|theo|by)\s*:\s*", "", re.sub(r"\s+", " ", text).strip(), flags=re.I).strip()
    match = CREDIT_REGEX.search(text)
    if match:
        text = text[:match.start()].strip()
    return text if (text and text.lower() not in {"vnexpress", "vnexpress.net", "báo vnexpress"}) else None


def get_author_element(container: Tag) -> Tag | None:
    """Xác định thẻ HTML <p> chứa tên tác giả nằm gần cuối bài viết."""
    end_marker = container.select_one("#article-end")
    cands = [s for s in end_marker.previous_siblings if isinstance(s, Tag) and s.name == "p"][:5] if end_marker else container.find_all("p")[-5:]
    for p in cands:
        t = p.get_text(" ", strip=True)
        align = str(p.get("align", "") or p.get("style", "")).lower()
        if "right" in align or p.find(["strong", "b"]) or re.search(r"\((?:theo|ảnh|nguồn|tổng hợp)", t, re.I):
            cleaned = clean_author(t)
            if cleaned and len(cleaned) <= 120 and not cleaned.lower().startswith(("ảnh:", "video:", "hotline:", "email:")):
                return p
    return None


def extract_author(soup: BeautifulSoup) -> str | None:
    """Bóc tách tên tác giả hoặc bút danh phóng viên từ cấu trúc DOM bài viết."""
    container = soup.select_one(".fck_detail")
    if container and (el := get_author_element(container)) is not None:
        if cleaned := clean_author(el.get_text(" ", strip=True)):
            return cleaned
    for sel in [".author_name", ".author-name", ".article-author", "p.author"]:
        if (el := soup.select_one(sel)) and (cleaned := clean_author(el.get_text(" ", strip=True))):
            return cleaned
    for el in soup.find_all(string=re.compile(r"^\s*(Tác giả|Tac gia|By)\s*:", re.I)):
        if el.parent and (cleaned := clean_author(el.parent.get_text(" ", strip=True))):
            return cleaned
    return None


def extract_article_content(soup: BeautifulSoup) -> str:
    """Bóc tách nội dung chính của bài báo, lọc bỏ tiêu đề lặp lại, quảng cáo và đoạn tác giả."""
    container = soup.select_one(".fck_detail")
    if not container:
        return ""
    title = soup.select_one("h1.title-detail") or soup.find("h1")
    desc = soup.select_one("p.description")
    excluded = {re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() for el in (title, desc) if el}
    author_el = get_author_element(container)
    author_text = extract_author(soup)
    end_marker = container.select_one("#article-end")

    paragraphs: list[str] = []
    prev_text: str | None = None
    for child in container.children:
        if not isinstance(child, Tag):
            continue
        if end_marker and child is end_marker:
            break
        if (author_el and child is author_el) or child.name in ("script", "style", "iframe", "noscript", "button", "h1"):
            continue
        if child.name == "p" and "description" in (child.get("class") or []):
            continue
        text = re.sub(r"\s+", " ", child.get_text(" ", strip=True)).strip()
        if not text or text in excluded or text == prev_text:
            continue
        if author_text and (text == author_text or clean_author(text) == author_text):
            continue
        paragraphs.append(text)
        prev_text = text
    return "\n".join(paragraphs)


def get_meta(soup: BeautifulSoup, **attrs) -> str | None:
    """Trích xuất thuộc tính 'content' từ thẻ <meta> phù hợp."""
    tag = soup.find("meta", attrs=attrs)
    return str(tag["content"]).strip() if (tag and tag.get("content")) else None


def extract_category_from_url(url: str) -> str | None:
    """Nhận diện tên chuyên mục chuẩn hóa từ đường dẫn URL VnExpress."""
    return next((cat for path, cat in CATEGORY_PATHS.items() if path in url), None)


def extract_article_id(soup: BeautifulSoup, url: str) -> str | None:
    """Trích xuất ID bài viết số tự nhiên từ thẻ meta tt_article_id hoặc từ đuôi URL."""
    tag = soup.find("meta", attrs={"name": "tt_article_id"})
    if tag and tag.get("content"):
        return str(tag["content"]).strip()
    match = re.search(r"/(\d+)\.html(?:$|\?)", url)
    return match.group(1) if match else None


def extract_published_at(soup: BeautifulSoup, rss_metadata: dict | None = None) -> str | None:
    """Trích xuất thời điểm xuất bản bài báo theo chuẩn ISO 8601 từ thẻ meta hoặc RSS."""
    for attrs in [{"name": "pubdate"}, {"itemprop": "datePublished"}, {"property": "article:published_time"}]:
        if (tag := soup.find("meta", attrs=attrs)) and tag.get("content"):
            return str(tag["content"]).strip()
    return (rss_metadata or {}).get("published_at")


class ArticleCrawler:
    """Lớp điều phối thu thập và bóc tách cấu trúc bài viết từ trang tin VnExpress."""

    # Tham chiếu tĩnh tới clean_author và get_author_element phục vụ tính tương thích test
    clean_author = staticmethod(clean_author)
    get_author_element = staticmethod(get_author_element)

    def fetch(self, url: str) -> str:
        """Tải mã nguồn HTML của bài viết từ URL."""
        return fetch_url(url)

    def extract_author(self, soup: BeautifulSoup) -> str | None:
        """Bóc tách tác giả bài viết."""
        return extract_author(soup)

    def extract_article_content(self, soup: BeautifulSoup) -> str:
        """Bóc tách văn bản nội dung thân bài."""
        return extract_article_content(soup)

    def parse(self, html: str | None, url: str, rss_metadata: dict | None = None) -> dict[str, Any]:
        """Phân tích HTML và trả về bản ghi 12 trường dữ liệu thô."""
        soup = BeautifulSoup(html or "", "lxml")
        rss = rss_metadata or {}
        t_el = soup.select_one("h1.title-detail") or soup.find("h1")
        d_el = soup.select_one("p.description")
        return {
            "url": url,
            "title": t_el.get_text(" ", strip=True) if t_el else (get_meta(soup, property="og:title") or rss.get("title")),
            "description": d_el.get_text(" ", strip=True) if d_el else (get_meta(soup, property="og:description") or rss.get("description")),
            "content": self.extract_article_content(soup),
            "author": self.extract_author(soup),
            "publisher": "VnExpress",
            "published_at": extract_published_at(soup, rss),
            "category": rss.get("category") or extract_category_from_url(url),
            "subcategory": get_meta(soup, itemprop="articleSection"),
            "article_id": extract_article_id(soup, url),
            "crawled_at": datetime.now(timezone.utc).isoformat(),
            "source": "vnexpress",
        }

    def crawl(self, url: str, rss_metadata: dict | None = None) -> dict[str, Any]:
        """Tải trang và bóc tách hoàn chỉnh dữ liệu bài báo."""
        return self.parse(html=self.fetch(url), url=url, rss_metadata=rss_metadata)


class RSSCrawler:
    """Lớp quét và trích xuất danh sách liên kết bài viết từ các luồng RSS của VnExpress."""

    def fetch_feed(self, url: str) -> str:
        """Tải tệp XML RSS từ địa chỉ web."""
        return fetch_url(url)

    def parse_feed(self, xml_text: str, category: str) -> list[dict[str, Any]]:
        """Phân tích cú pháp RSS XML để lấy danh sách bài viết kèm metadata."""
        try:
            root = ET.fromstring(xml_text)
        except (ET.ParseError, TypeError, ValueError) as exc:
            logger.warning("Lỗi phân tích cú pháp XML RSS (%s): %s", category, exc)
            return []
        articles: list[dict[str, Any]] = []
        for item in root.iter("item"):
            def get_text_tag(tag_name: str) -> str | None:
                el = item.find(tag_name)
                return el.text.strip() if el is not None and el.text else None

            if url := get_text_tag("link"):
                articles.append({
                    "url": url,
                    "title": get_text_tag("title"),
                    "description": get_text_tag("description"),
                    "published_at": get_text_tag("pubDate"),
                    "category": category,
                    "categories": [category],
                })
        return articles

    def discover(self) -> list[dict[str, Any]]:
        """Quét và gom nhóm các bài viết từ 5 luồng RSS chuyên mục mục tiêu."""
        discovered: dict[str, dict[str, Any]] = {}
        for category, feed_url in RSS_FEEDS.values():
            try:
                for a in self.parse_feed(fetch_url(feed_url), category):
                    url = a["url"]
                    if "vnexpress.net" in url:
                        if url not in discovered:
                            discovered[url] = a
                        elif category not in discovered[url].setdefault("categories", []):
                            discovered[url]["categories"].append(category)
            except Exception as exc:
                logger.warning("Không thể xử lý RSS feed %s: %s", feed_url, exc)
        return list(discovered.values())


class SitemapCrawler:
    """Lớp quét danh sách liên kết bài viết từ Sitemap XML của VnExpress."""

    def discover(self) -> list[str]:
        """Duyệt và trích xuất tất cả các URL bài báo kết thúc bằng .html từ sitemap XML."""
        discovered: set[str] = set()
        for sitemap_url in SITEMAP_URLS:
            try:
                root = ET.fromstring(fetch_url(sitemap_url))
                discovered.update(
                    el.text.strip() for el in root.iter()
                    if el.tag.endswith("loc") and el.text and "vnexpress.net" in el.text and el.text.strip().endswith(".html")
                )
            except Exception as exc:
                logger.warning("Không thể xử lý sitemap %s: %s", sitemap_url, exc)
        return sorted(discovered)


def save_record(path: Path, record: dict[str, Any]) -> None:
    """Ghi bổ sung một bản ghi vào tệp JSON Lines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_crawled_urls(path: Path) -> set[str]:
    """Đọc danh sách các URL bài viết đã được cào trước đó để tránh cào trùng."""
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as f:
        return {u for line in f if line.strip() and (u := json.loads(line).get("url"))}


def select_balanced_articles(articles: list[dict[str, Any]], max_articles: int = MAX_ARTICLES, articles_per_category: int = 4) -> list[dict[str, Any]]:
    """Chọn lọc mẫu bài viết phân bổ đều trên 5 chuyên mục mục tiêu."""
    grouped = defaultdict(list)
    for a in articles:
        if a.get("category"):
            grouped[a["category"]].append(a)
    return [a for cat, _ in RSS_FEEDS.values() for a in grouped.get(cat, [])[:articles_per_category]][:max_articles]


def main() -> None:
    """Hàm điều phối toàn bộ quá trình cào bài viết tự động."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    rss_crawler = RSSCrawler()
    article_crawler = ArticleCrawler()
    discovered = rss_crawler.discover()
    pending = [a for a in discovered if a["url"] not in load_crawled_urls(ARTICLE_OUTPUT)]
    selected = select_balanced_articles(pending, MAX_ARTICLES, articles_per_category=4)

    logger.info("Tìm thấy %d bài chờ, tiến hành cào %d bài...", len(pending), len(selected))
    success, failed = 0, 0
    for idx, meta in enumerate(selected, start=1):
        url = meta["url"]
        logger.info("[%d/%d] Đang cào: %s", idx, len(selected), url)
        try:
            art = article_crawler.crawl(url, rss_metadata=meta)
            save_record(ARTICLE_OUTPUT, art)
            save_record(CRAWL_LOG_OUTPUT, {"url": url, "status": "success", "timestamp": datetime.now(timezone.utc).isoformat()})
            success += 1
        except Exception as exc:
            failed += 1
            logger.warning("Thất bại khi cào %s: %s", url, exc)
            save_record(CRAWL_LOG_OUTPUT, {"url": url, "status": "failed", "error": str(exc), "timestamp": datetime.now(timezone.utc).isoformat()})
        time.sleep(REQUEST_DELAY)
    logger.info("Hoàn tất cào: %d thành công, %d thất bại", success, failed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()