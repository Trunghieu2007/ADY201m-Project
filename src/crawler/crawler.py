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

# Paths & Feed Configurations
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

REQUEST_TIMEOUT, REQUEST_DELAY, MAX_ARTICLES = 20, 1.0, 20
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154.0.0.0 VnExpressDataScienceCrawler/0.1"
CREDIT_REGEX = re.compile(r"\s+(?:nhóm\s+thiết\s+kế|kết\s+cấu|đơn\s+vị\s+thi\s+công|ảnh|photo|photos|thiết\s+kế|\"?biên\s+tập\"?|biên\s+dịch)\s*:", re.I)
CATEGORY_PATHS = {
    "/thoi-su/": "Thời sự",
    "/kinh-doanh/": "Kinh doanh",
    "/bat-dong-san/": "Bất động sản",
    "/suc-khoe/": "Sức khỏe",
    "/khoa-hoc-cong-nghe/": "Khoa học công nghệ",
}


def fetch_url(url: str, retries: int = 3, delay: float = 1.0) -> str:
    """Tải nội dung HTML/XML với cơ chế retry và xử lý ngoại lệ RequestException."""
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


class ArticleCrawler:
    """Thu thập và bóc tách cấu trúc nội dung bài viết từ VnExpress."""

    def fetch(self, url: str) -> str:
        return fetch_url(url)

    @staticmethod
    def clean_author(text: str | None) -> str | None:
        if not text:
            return None
        text = re.sub(r"^(tác giả|tac gia|theo|by)\s*:\s*", "", re.sub(r"\s+", " ", text).strip(), flags=re.I).strip()
        m = CREDIT_REGEX.search(text)
        if m:
            text = text[:m.start()].strip()
        return text if (text and text.lower() not in {"vnexpress", "vnexpress.net", "báo vnexpress"}) else None

    @staticmethod
    def get_author_element(container: Tag) -> Tag | None:
        end_marker = container.select_one("#article-end")
        cands = [s for s in end_marker.previous_siblings if isinstance(s, Tag) and s.name == "p"][:5] if end_marker else container.find_all("p")[-5:]
        for p in cands:
            t = p.get_text(" ", strip=True)
            align = str(p.get("align", "") or p.get("style", "")).lower()
            if "right" in align or p.find(["strong", "b"]) or re.search(r"\((?:theo|ảnh|nguồn|tổng hợp)", t, re.I):
                cleaned = ArticleCrawler.clean_author(t)
                if cleaned and len(cleaned) <= 120 and not cleaned.lower().startswith(("ảnh:", "video:", "hotline:", "email:")):
                    return p
        return None

    @staticmethod
    def extract_author(soup: BeautifulSoup) -> str | None:
        container = soup.select_one(".fck_detail")
        if container and (el := ArticleCrawler.get_author_element(container)) is not None:
            if cleaned := ArticleCrawler.clean_author(el.get_text(" ", strip=True)):
                return cleaned
        for sel in [".author_name", ".author-name", ".article-author", "p.author"]:
            if (el := soup.select_one(sel)) and (cleaned := ArticleCrawler.clean_author(el.get_text(" ", strip=True))):
                return cleaned
        for el in soup.find_all(string=re.compile(r"^\s*(Tác giả|Tac gia|By)\s*:", re.I)):
            if el.parent and (cleaned := ArticleCrawler.clean_author(el.parent.get_text(" ", strip=True))):
                return cleaned
        return None

    @staticmethod
    def extract_article_content(soup: BeautifulSoup) -> str:
        container = soup.select_one(".fck_detail")
        if not container:
            return ""
        title, desc = soup.select_one("h1.title-detail") or soup.find("h1"), soup.select_one("p.description")
        excluded = {re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() for el in (title, desc) if el}
        author_el, author_text = ArticleCrawler.get_author_element(container), ArticleCrawler.extract_author(soup)
        end_marker = container.select_one("#article-end")

        paragraphs, prev = [], None
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
        return str(tag["content"]).strip() if (tag and tag.get("content")) else None

    @staticmethod
    def extract_category_from_url(url: str) -> str | None:
        return next((cat for path, cat in CATEGORY_PATHS.items() if path in url), None)

    @staticmethod
    def extract_article_id(soup: BeautifulSoup, url: str) -> str | None:
        tag = soup.find("meta", attrs={"name": "tt_article_id"})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
        m = re.search(r"/(\d+)\.html(?:$|\?)", url)
        return m.group(1) if m else None

    @staticmethod
    def extract_published_at(soup: BeautifulSoup, rss_metadata: dict | None = None) -> str | None:
        for attrs in [{"name": "pubdate"}, {"itemprop": "datePublished"}, {"property": "article:published_time"}]:
            if (tag := soup.find("meta", attrs=attrs)) and tag.get("content"):
                return str(tag["content"]).strip()
        return (rss_metadata or {}).get("published_at")

    def parse(self, html: str | None, url: str, rss_metadata: dict | None = None) -> dict:
        soup, rss = BeautifulSoup(html or "", "lxml"), rss_metadata or {}
        t_el, d_el = soup.select_one("h1.title-detail") or soup.find("h1"), soup.select_one("p.description")
        return {
            "url": url,
            "title": t_el.get_text(" ", strip=True) if t_el else (self.get_meta(soup, property="og:title") or rss.get("title")),
            "description": d_el.get_text(" ", strip=True) if d_el else (self.get_meta(soup, property="og:description") or rss.get("description")),
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


class RSSCrawler:
    """Quét và trích xuất danh sách liên kết bài viết từ RSS feeds."""

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
            def get_t(tag: str) -> str | None:
                el = item.find(tag)
                return el.text.strip() if el is not None and el.text else None

            if url := get_t("link"):
                articles.append({
                    "url": url,
                    "title": get_t("title"),
                    "description": get_t("description"),
                    "published_at": get_t("pubDate"),
                    "category": category,
                    "categories": [category],
                })
        return articles

    def discover(self) -> list[dict]:
        discovered: dict[str, dict] = {}
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
    """Quét và trích xuất liên kết bài viết từ Sitemap XML."""

    def discover(self) -> list[str]:
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


def save_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_crawled_urls(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as f:
        return {u for line in f if line.strip() and (u := json.loads(line).get("url"))}


def select_balanced_articles(articles: list[dict], max_articles: int = MAX_ARTICLES, articles_per_category: int = 4) -> list[dict]:
    grouped = defaultdict(list)
    for a in articles:
        if a.get("category"):
            grouped[a["category"]].append(a)
    return [a for cat, _ in RSS_FEEDS.values() for a in grouped.get(cat, [])[:articles_per_category]][:max_articles]


def main() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    rss_crawler, article_crawler = RSSCrawler(), ArticleCrawler()
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
            save_jsonl(ARTICLE_OUTPUT, art)
            save_jsonl(CRAWL_LOG_OUTPUT, {"url": url, "status": "success", "timestamp": datetime.now(timezone.utc).isoformat()})
            success += 1
        except Exception as exc:
            failed += 1
            logger.warning("Thất bại khi cào %s: %s", url, exc)
            save_jsonl(CRAWL_LOG_OUTPUT, {"url": url, "status": "failed", "error": str(exc), "timestamp": datetime.now(timezone.utc).isoformat()})
        time.sleep(REQUEST_DELAY)
    logger.info("Hoàn tất: %d thành công, %d thất bại", success, failed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()