from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import requests
from .config import REQUEST_RETRIES, REQUEST_RETRY_BACKOFF, REQUEST_TIMEOUT, SITEMAP_URLS, USER_AGENT

logger = logging.getLogger(__name__)


class SitemapCrawler:
    # Quét và thu thập các liên kết bài viết từ tập tin Sitemap XML

    def __init__(self) -> None:
        # Khởi tạo session với headers định danh
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/xml,text/xml,*/*"})

    def fetch_sitemap(self, sitemap_url: str) -> str:
        # Tải tập tin Sitemap XML từ máy chủ VnExpress kèm thử lại
        logger.info("Downloading sitemap: %s", sitemap_url)
        last_error: requests.RequestException | None = None
        for attempt in range(1, REQUEST_RETRIES + 1):
            try:
                response = self.session.get(sitemap_url, timeout=REQUEST_TIMEOUT)
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
        raise RuntimeError("Sitemap fetch failed without a response")

    @staticmethod
    def parse_urls(xml_text: str) -> list[str]:
        # Trích xuất các thẻ loc từ mã XML của sitemap
        root = ET.fromstring(xml_text)
        urls: list[str] = []
        for element in root.iter():
            if element.tag.endswith("loc") and element.text:
                url = element.text.strip()
                if url:
                    urls.append(url)
        return list(dict.fromkeys(urls))

    @staticmethod
    def is_vnexpress_url(url: str) -> bool:
        # Xác minh URL thuộc tên miền VnExpress
        hostname = urlparse(url).hostname
        if hostname is None:
            return False
        hostname = hostname.lower()
        return hostname == "vnexpress.net" or hostname.endswith(".vnexpress.net")

    def discover(self) -> list[str]:
        # Khám phá danh sách URL từ toàn bộ các sitemap đã cấu hình
        discovered: set[str] = set()
        for sitemap_url in SITEMAP_URLS:
            try:
                xml_text = self.fetch_sitemap(sitemap_url)
                urls = self.parse_urls(xml_text)
                valid_urls = {
                    url for url in urls
                    if self.is_vnexpress_url(url) and urlparse(url).path.lower().endswith(".html")
                }
                discovered.update(valid_urls)
            except Exception:
                logger.exception("Failed to process sitemap: %s", sitemap_url)
        return sorted(discovered)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    crawler = SitemapCrawler()
    discovered_urls = crawler.discover()
    print(f"Discovered URLs: {len(discovered_urls)}")