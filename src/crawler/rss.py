from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import requests
from .config import REQUEST_RETRIES, REQUEST_RETRY_BACKOFF, REQUEST_TIMEOUT, RSS_FEEDS, USER_AGENT

logger = logging.getLogger(__name__)


class RSSCrawler:
    # Quét và thu thập các liên kết bài viết từ nguồn cấp RSS VnExpress

    def __init__(self) -> None:
        # Khởi tạo session tải RSS
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        })

    def fetch_feed(self, url: str) -> str:
        # Tải nội dung XML của luồng RSS kèm cơ chế thử lại khi gặp lỗi
        logger.info("Downloading RSS: %s", url)
        last_error: requests.RequestException | None = None
        for attempt in range(1, REQUEST_RETRIES + 1):
            try:
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                if 500 <= response.status_code < 600 and attempt < REQUEST_RETRIES:
                    time.sleep(REQUEST_RETRY_BACKOFF * attempt)
                    continue
                response.raise_for_status()
                return response.text
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_error = exc
                if attempt >= REQUEST_RETRIES:
                    raise
                time.sleep(REQUEST_RETRY_BACKOFF * attempt)
        if last_error is not None:
            raise last_error
        raise RuntimeError("RSS fetch failed without a response")

    @staticmethod
    def parse_feed(xml_text: str, category: str) -> list[dict]:
        # Phân tích cú pháp XML của RSS thành danh sách bài viết sơ bộ
        root = ET.fromstring(xml_text)
        articles: list[dict] = []
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

    @staticmethod
    def is_vnexpress_url(url: str) -> bool:
        # Kiểm tra tính hợp lệ của tên miền VnExpress
        hostname = urlparse(url).hostname
        if hostname is None:
            return False
        hostname = hostname.lower()
        return hostname == "vnexpress.net" or hostname.endswith(".vnexpress.net")

    def discover(self) -> list[dict]:
        # Quét toàn bộ RSS feeds đã cấu hình và hợp nhất bài viết không trùng lặp
        discovered: dict[str, dict] = {}
        for _feed_key, (category, feed_url) in RSS_FEEDS.items():
            try:
                xml_text = self.fetch_feed(feed_url)
                articles = self.parse_feed(xml_text=xml_text, category=category)
                for article in articles:
                    url = article["url"]
                    if not self.is_vnexpress_url(url):
                        continue
                    if url not in discovered:
                        discovered[url] = article
                        continue
                    existing = discovered[url]
                    cats = existing.setdefault("categories", [])
                    if category not in cats:
                        cats.append(category)
            except Exception:
                logger.exception("Failed to process RSS feed: %s", feed_url)
        logger.info("Total unique RSS articles: %d", len(discovered))
        return list(discovered.values())