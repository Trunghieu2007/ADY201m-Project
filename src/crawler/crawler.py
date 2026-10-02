from __future__ import annotations

import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. Cấu hình đường dẫn & Nguồn cấp dữ liệu
# ==============================================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
ARTICLE_OUTPUT = RAW_DATA_DIR / "articles.jsonl"
CRAWL_LOG_OUTPUT = RAW_DATA_DIR / "crawl_log.jsonl"

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

REQUEST_TIMEOUT = 20
REQUEST_DELAY = 1.0
MAX_ARTICLES = 20
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/154.0.0.0 Safari/537.36 VnExpressDataScienceCrawler/0.1"
)

CREDIT_REGEX = re.compile(
    r"\s+(?:nhóm\s+thiết\s+kế|kết\s+cấu|đơn\s+vị\s+thi\s+công|ảnh|photo|photos|thiết\s+kế|\"?biên\s+tập\"?|biên\s+dịch)\s*:",
    re.IGNORECASE,
)


# ==============================================================================
# 2. Hàm hỗ trợ tải trang (HTTP Helper)
# ==============================================================================
def fetch_url(url: str, retries: int = 3, delay: float = 1.0) -> str:
    """Tải nội dung văn bản từ URL với cơ chế thử lại (retry) và bắt lỗi toàn diện."""
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8"}
    for attempt in range(1, retries + 1):
        try:
            res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            res.raise_for_status()
            return res.text
        except requests.RequestException as exc:
            if attempt == retries:
                logger.error("Đã hết số lần thử lại (%d/%d) khi tải %s: %s", attempt, retries, url, exc)
                raise
            logger.warning("Lần thử %d/%d tải %s gặp lỗi: %s. Thử lại sau %.1fs...", attempt, retries, url, exc, delay * attempt)
            time.sleep(delay * attempt)
    return ""


# ==============================================================================
# 3. Trích xuất & Bóc tách Bài viết (Article Parser)
# ==============================================================================
class ArticleCrawler:
    """Bóc tách và thu thập dữ liệu bài viết từ VnExpress."""

    def __init__(self) -> None:
        pass

    def fetch(self, url: str) -> str:
        return fetch_url(url)

    @staticmethod
    def clean_author(text: str | None) -> str | None:
        """Làm sạch tên tác giả và loại bỏ các chú thích ảnh/biên dịch."""
        if not text:
            return None
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"^(tác giả|tac gia|theo|by)\s*:\s*", "", text, flags=re.IGNORECASE).strip()
        match = CREDIT_REGEX.search(text)
        if match:
            text = text[:match.start()].strip()
        if not text or text.lower() in {"vnexpress", "vnexpress.net", "báo vnexpress"}:
            return None
        return text

    @staticmethod
    def get_author_element(container: Tag) -> Tag | None:
        """Tìm thẻ đoạn văn chứa tên tác giả nằm trước thẻ #article-end."""
        end_marker = container.select_one("#article-end")
        candidates = []
        if end_marker:
            for s in end_marker.previous_siblings:
                if isinstance(s, Tag) and s.name == "p":
                    candidates.append(s)
                    if len(candidates) >= 5:
                        break
        else:
            candidates = container.find_all("p")[-5:]

        for p in candidates:
            t = p.get_text(" ", strip=True)
            align = p.get("align", "") or p.get("style", "")
            is_align_right = "right" in str(align).lower()
            has_strong = p.find(["strong", "b"]) is not None
            has_credit = bool(re.search(r"\((?:theo|ảnh|nguồn|tổng hợp)", t, re.I))
            if is_align_right or has_strong or has_credit:
                cleaned = ArticleCrawler.clean_author(t)
                if cleaned and len(cleaned) <= 120 and not cleaned.lower().startswith(("ảnh:", "video:", "hotline:", "email:")):
                    return p
        return None

    @staticmethod
    def extract_author(soup: BeautifulSoup) -> str | None:
        """Bóc tách tên tác giả bài báo từ container bài viết hoặc selector dự phòng."""
        container = soup.select_one(".fck_detail")
        if container:
            author_el = ArticleCrawler.get_author_element(container)
            if author_el is not None:
                cleaned = ArticleCrawler.clean_author(author_el.get_text(" ", strip=True))
                if cleaned:
                    return cleaned

        for sel in [".author_name", ".author-name", ".article-author", "p.author"]:
            el = soup.select_one(sel)
            if el:
                cleaned = ArticleCrawler.clean_author(el.get_text(" ", strip=True))
                if cleaned:
                    return cleaned

        label_pattern = re.compile(r"^\s*(Tác giả|Tac gia|By)\s*:", flags=re.IGNORECASE)
        for el in soup.find_all(string=label_pattern):
            if el.parent is not None:
                cleaned = ArticleCrawler.clean_author(el.parent.get_text(" ", strip=True))
                if cleaned:
                    return cleaned
        return None

    @staticmethod
    def extract_article_content(soup: BeautifulSoup) -> str:
        """Trích xuất nội dung văn bản chính trong .fck_detail, loại trừ quảng cáo và rác."""
        container = soup.select_one(".fck_detail")
        if not container:
            return ""
        title = soup.select_one("h1.title-detail") or soup.find("h1")
        desc = soup.select_one("p.description")
        excluded = {re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() for el in (title, desc) if el}

        author_el = ArticleCrawler.get_author_element(container)
        author_text = ArticleCrawler.extract_author(soup)
        end_marker = container.select_one("#article-end")

        paragraphs = []
        prev = None
        for child in container.children:
            if not isinstance(child, Tag):
                continue
            if end_marker and child is end_marker:
                break
            if author_el and child is author_el:
                continue
            if child.name in ("script", "style", "iframe", "noscript", "button"):
                continue
            if child.name == "h1":
                continue
            if child.name == "p" and "description" in (child.get("class") or []):
                continue

            text = re.sub(r"\s+", " ", child.get_text(" ", strip=True)).strip()
            if not text or text in excluded or text == prev:
                continue
            if author_text and (text == author_text or ArticleCrawler.clean_author(text) == author_text):
                continue
            paragraphs.append(text)
            prev = text
        return "\n".join(paragraphs)

    @staticmethod
    def get_meta(soup: BeautifulSoup, **attrs) -> str | None:
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            val = str(tag["content"]).strip()
            return val if val else None
        return None

    @staticmethod
    def extract_category_from_url(url: str) -> str | None:
        category_paths = {
            "/thoi-su/": "Thời sự",
            "/kinh-doanh/": "Kinh doanh",
            "/bat-dong-san/": "Bất động sản",
            "/suc-khoe/": "Sức khỏe",
            "/khoa-hoc-cong-nghe/": "Khoa học công nghệ",
        }
        for path, cat in category_paths.items():
            if path in url:
                return cat
        return None

    @staticmethod
    def extract_article_id(soup: BeautifulSoup, url: str) -> str | None:
        tag = soup.find("meta", attrs={"name": "tt_article_id"})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
        m = re.search(r"/(\d+)\.html(?:$|\?)", url)
        return m.group(1) if m else None

    @staticmethod
    def extract_published_at(soup: BeautifulSoup, rss_metadata: dict | None = None) -> str | None:
        rss = rss_metadata or {}
        for attrs in [{"name": "pubdate"}, {"itemprop": "datePublished"}, {"property": "article:published_time"}]:
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                return str(tag["content"]).strip()
        return rss.get("published_at")

    def parse(self, html: str | None, url: str, rss_metadata: dict | None = None) -> dict:
        """Phân tích HTML bài viết thành dictionary có cấu trúc."""
        soup = BeautifulSoup(html or "", "lxml")
        rss = rss_metadata or {}
        title_el = soup.select_one("h1.title-detail") or soup.find("h1")
        title = title_el.get_text(" ", strip=True) if title_el else (self.get_meta(soup, property="og:title") or rss.get("title"))
        desc_el = soup.select_one("p.description")
        desc = desc_el.get_text(" ", strip=True) if desc_el else (self.get_meta(soup, property="og:description") or rss.get("description"))

        return {
            "url": url,
            "title": title,
            "description": desc,
            "content": self.extract_article_content(soup),
            "author": self.extract_author(soup),
            "publisher": "VnExpress",
            "published_at": self.extract_published_at(soup, rss),
            "category": rss.get("category") or self.extract_category_from_url(url),
            "subcategory": self.get_meta(soup, itemprop="articleSection"),
            "article_id": self.extract_article_id(soup, url),
            "crawled_at": datetime.now(timezone.utc).isoformat(),
            "source": "vnexpress",
        }

    def crawl(self, url: str, rss_metadata: dict | None = None) -> dict:
        return self.parse(html=self.fetch(url), url=url, rss_metadata=rss_metadata)


# ==============================================================================
# 4. Quét nguồn RSS & Sitemap (Discovery)
# ==============================================================================
class RSSCrawler:
    """Quét và thu thập liên kết bài viết từ RSS feeds."""

    def __init__(self) -> None:
        pass

    def fetch_feed(self, url: str) -> str:
        return fetch_url(url)

    @staticmethod
    def parse_feed(xml_text: str, category: str) -> list[dict]:
        try:
            root = ET.fromstring(xml_text)
        except (ET.ParseError, TypeError, ValueError) as exc:
            logger.warning("Lỗi phân tích cú pháp XML RSS (%s): %s", category, exc)
            return []
        articles = []
        for item in root.iter("item"):
            def get_text(tag: str) -> str | None:
                el = item.find(tag)
                return el.text.strip() if el is not None and el.text else None

            url = get_text("link")
            if not url:
                continue
            articles.append({
                "url": url,
                "title": get_text("title"),
                "description": get_text("description"),
                "published_at": get_text("pubDate"),
                "category": category,
                "categories": [category],
            })
        return articles

    def discover(self) -> list[dict]:
        discovered: dict[str, dict] = {}
        for category, feed_url in RSS_FEEDS.values():
            try:
                xml_text = fetch_url(feed_url)
                for article in self.parse_feed(xml_text, category):
                    url = article["url"]
                    if "vnexpress.net" in url:
                        if url not in discovered:
                            discovered[url] = article
                        else:
                            cats = discovered[url].setdefault("categories", [])
                            if category not in cats:
                                cats.append(category)
            except Exception as exc:
                logger.warning("Failed to process RSS feed %s: %s", feed_url, exc)
        return list(discovered.values())


class SitemapCrawler:
    """Quét và thu thập liên kết bài viết từ Sitemap XML."""

    def __init__(self) -> None:
        pass

    def discover(self) -> list[str]:
        discovered: set[str] = set()
        for sitemap_url in SITEMAP_URLS:
            try:
                xml_text = fetch_url(sitemap_url)
                root = ET.fromstring(xml_text)
                for el in root.iter():
                    if el.tag.endswith("loc") and el.text:
                        u = el.text.strip()
                        if "vnexpress.net" in u and u.endswith(".html"):
                            discovered.add(u)
            except Exception as exc:
                logger.warning("Failed to process sitemap %s: %s", sitemap_url, exc)
        return sorted(discovered)


# ==============================================================================
# 5. Lưu trữ & Điều phối Quy trình chính (Orchestrator)
# ==============================================================================
def save_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_crawled_urls(path: Path) -> set[str]:
    if not path.exists():
        return set()
    urls = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    urls.add(json.loads(line).get("url"))
                except Exception:
                    pass
    return urls


def select_balanced_articles(articles: list[dict], max_articles: int = MAX_ARTICLES, articles_per_category: int = 4) -> list[dict]:
    grouped = defaultdict(list)
    for a in articles:
        if a.get("category"):
            grouped[a["category"]].append(a)
    selected = []
    for cat, _ in RSS_FEEDS.values():
        selected.extend(grouped.get(cat, [])[:articles_per_category])
    return selected[:max_articles]


def main() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    rss_crawler = RSSCrawler()
    article_crawler = ArticleCrawler()

    logger.info("Discovering articles from RSS feeds...")
    discovered = rss_crawler.discover()
    crawled_urls = load_crawled_urls(ARTICLE_OUTPUT)
    pending = [a for a in discovered if a["url"] not in crawled_urls]
    selected = select_balanced_articles(pending, MAX_ARTICLES, articles_per_category=4)

    logger.info("Found %d pending articles, crawling %d...", len(pending), len(selected))
    success, failed = 0, 0
    for idx, meta in enumerate(selected, start=1):
        url = meta["url"]
        logger.info("[%d/%d] Crawling: %s", idx, len(selected), url)
        try:
            art = article_crawler.crawl(url, rss_metadata=meta)
            save_jsonl(ARTICLE_OUTPUT, art)
            save_jsonl(CRAWL_LOG_OUTPUT, {"url": url, "status": "success", "timestamp": datetime.now(timezone.utc).isoformat()})
            success += 1
        except Exception as exc:
            failed += 1
            logger.warning("Failed to crawl %s: %s", url, exc)
            save_jsonl(CRAWL_LOG_OUTPUT, {"url": url, "status": "failed", "error": str(exc), "timestamp": datetime.now(timezone.utc).isoformat()})
        time.sleep(REQUEST_DELAY)
    logger.info("Crawl finished: %d success, %d failed", success, failed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()