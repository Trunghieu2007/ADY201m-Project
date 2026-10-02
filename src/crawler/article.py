from __future__ import annotations

import re
import time
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup, Tag
from .config import REQUEST_RETRIES, REQUEST_RETRY_BACKOFF, REQUEST_TIMEOUT, USER_AGENT


class ArticleCrawler:
    # Bóc tách và thu thập dữ liệu bài viết từ VnExpress

    def __init__(self) -> None:
        # Khởi tạo HTTP session có sẵn headers
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        })

    def fetch(self, url: str) -> str:
        # Tải trang bài viết và trả về mã nguồn HTML thô kèm cơ chế retry
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
        raise RuntimeError("HTTP fetch failed without a response")

    @staticmethod
    def normalize_text(element: Tag | None) -> str | None:
        # Chuẩn hóa khoảng trắng của văn bản trích xuất từ thẻ HTML
        if element is None:
            return None
        text = re.sub(r"\s+", " ", element.get_text(" ", strip=True)).strip()
        return text if text else None

    @staticmethod
    def get_meta(soup: BeautifulSoup, *, name: str | None = None, property: str | None = None, itemprop: str | None = None) -> str | None:
        # Trích xuất thuộc tính content từ thẻ meta HTML
        element = None
        if name is not None:
            element = soup.find("meta", attrs={"name": name})
        elif property is not None:
            element = soup.find("meta", attrs={"property": property})
        elif itemprop is not None:
            element = soup.find("meta", attrs={"itemprop": itemprop})
        if element is None:
            return None
        content = element.get("content")
        if not content:
            return None
        content = str(content).strip()
        return content if content else None

    @staticmethod
    def extract_category_from_url(url: str) -> str | None:
        # Nhận diện chuyên mục chính từ đường dẫn URL VnExpress
        category_paths = {
            "/thoi-su/": "Thời sự",
            "/kinh-doanh/": "Kinh doanh",
            "/bat-dong-san/": "Bất động sản",
            "/suc-khoe/": "Sức khỏe",
            "/khoa-hoc-cong-nghe/": "Khoa học công nghệ",
        }
        for path, category in category_paths.items():
            if path in url:
                return category
        return None

    @staticmethod
    def get_article_container(soup: BeautifulSoup) -> Tag | None:
        # Lấy container phần thân bài viết .fck_detail
        return soup.select_one(".fck_detail")

    @staticmethod
    def get_article_end(article_container: Tag) -> Tag | None:
        # Tìm thẻ mốc kết thúc bài viết #article-end
        return article_container.select_one("#article-end")

    @staticmethod
    def clean_author(text: str | None) -> str | None:
        # Làm sạch tên tác giả và loại bỏ các chú thích hậu kỳ
        if not text:
            return None
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"^(tác giả|tac gia|theo|by)\s*:\s*", "", text, flags=re.IGNORECASE).strip()
        credit_marker = re.search(
            r"\s+(?:(?:nhóm\s+thiết\s+kế)|kết\s+cấu|đơn\s+vị\s+thi\s+công|ảnh|photo|photos|thiết\s+kế|\"?biên\s+tập\"?|biên\s+dịch)\s*:",
            text,
            flags=re.IGNORECASE,
        )
        if credit_marker:
            text = text[:credit_marker.start()].strip()
        if not text or text.lower() in {"vnexpress", "vnexpress.net", "báo vnexpress"}:
            return None
        return text

    @staticmethod
    def is_right_aligned(element: Tag) -> bool:
        # Kiểm tra thẻ có căn lề phải (dấu hiệu của khối tác giả VnExpress)
        align = element.get("align")
        if isinstance(align, str) and align.strip().lower() == "right":
            return True
        style = element.get("style", "")
        if isinstance(style, str):
            normalized = re.sub(r"\s+", "", style.lower())
            if "text-align:right" in normalized:
                return True
        return False

    @staticmethod
    def contains_author_label(text: str) -> bool:
        # Kiểm tra chuỗi có tiền tố nhãn tác giả
        return bool(re.match(r"^\s*(tác giả|tac gia|by)\s*:", text, flags=re.IGNORECASE))

    @staticmethod
    def looks_like_metadata_or_credit(text: str) -> bool:
        # Loại bỏ các dòng chú thích ảnh hoặc thông tin liên hệ không phải tác giả
        lowered = text.lower().strip()
        rejected = (
            "ảnh:", "ảnh ", "photo:", "photos:", "phụ trách:", "phụ trách ",
            "thiết kế:", "thiết kế ", "địa điểm:", "website:", "hotline:",
            "email:", "nguồn:", "source:", "biên tập:", "biên dịch:"
        )
        return lowered.startswith(rejected)

    @staticmethod
    def is_strong_byline_candidate(element: Tag) -> bool:
        # Xác định đoạn văn có khả năng cao là phần ký tên tác giả
        text = ArticleCrawler.normalize_text(element)
        if not text or len(text) > 160 or ArticleCrawler.looks_like_metadata_or_credit(text):
            return False
        cleaned = ArticleCrawler.clean_author(text)
        if not cleaned:
            return False
        return ArticleCrawler.contains_author_label(text) or ArticleCrawler.is_right_aligned(element)

    @staticmethod
    def get_author_paragraph(article_container: Tag) -> Tag | None:
        # Tìm đoạn văn chứa tên tác giả nằm trước thẻ #article-end
        article_end = ArticleCrawler.get_article_end(article_container)
        if article_end is None:
            return None
        prev = article_end.find_previous_sibling()
        if isinstance(prev, Tag) and prev.name == "p" and ArticleCrawler.is_strong_byline_candidate(prev):
            return prev
        checked = 0
        for sibling in article_end.previous_siblings:
            if checked >= 6:
                break
            if not isinstance(sibling, Tag) or sibling.name != "p":
                continue
            if ArticleCrawler.is_strong_byline_candidate(sibling):
                return sibling
            checked += 1
        return None

    @staticmethod
    def extract_author(soup: BeautifulSoup) -> str | None:
        # Bóc tách tên tác giả bài báo VnExpress theo độ ưu tiên
        container = ArticleCrawler.get_article_container(soup)
        if container is not None:
            author_p = ArticleCrawler.get_author_paragraph(container)
            if author_p is not None:
                author = ArticleCrawler.clean_author(ArticleCrawler.normalize_text(author_p))
                if author:
                    return author
        fallback_selectors = [
            ".author_name", ".author-name", ".author-info-name", ".byline-name",
            ".article-author", ".article__author", "[class*='author-name']", "[class*='author_name']",
        ]
        for sel in fallback_selectors:
            for el in soup.select(sel):
                author = ArticleCrawler.clean_author(ArticleCrawler.normalize_text(el))
                if author and not ArticleCrawler.looks_like_metadata_or_credit(author) and len(author) <= 160:
                    return author
        label_pattern = re.compile(r"^\s*(Tác giả|Tac gia|By)\s*:", flags=re.IGNORECASE)
        for el in soup.find_all(string=label_pattern):
            if el.parent is not None:
                author = ArticleCrawler.clean_author(ArticleCrawler.normalize_text(el.parent))
                if author:
                    return author
        return None

    @staticmethod
    def extract_article_content(soup: BeautifulSoup) -> str:
        # Trích xuất nội dung văn bản chính trong .fck_detail, loại trừ tiêu đề, mô tả và tác giả
        container = ArticleCrawler.get_article_container(soup)
        if container is None:
            return ""
        article_end = ArticleCrawler.get_article_end(container)
        author_el = ArticleCrawler.get_author_paragraph(container)

        title_text = ArticleCrawler.normalize_text(soup.select_one("h1.title-detail")) or ArticleCrawler.normalize_text(soup.find("h1"))
        desc_text = ArticleCrawler.normalize_text(soup.select_one("p.description"))
        excluded = {v for v in (title_text, desc_text) if v}

        paragraphs: list[str] = []
        prev_text: str | None = None
        for child in container.children:
            if not isinstance(child, Tag):
                continue
            if article_end is not None and child is article_end:
                break
            if author_el is not None and child is author_el:
                continue
            if child.name == "h1":
                continue
            if child.name == "p" and "description" in (child.get("class") or []):
                continue
            if child.name in ("p", "figure") or True:
                text = ArticleCrawler.normalize_text(child)
                if text and text not in excluded and text != prev_text:
                    paragraphs.append(text)
                    prev_text = text
        return "\n".join(paragraphs)

    @staticmethod
    def extract_article_id(soup: BeautifulSoup, url: str) -> str | None:
        # Lấy định danh bài viết từ thẻ meta hoặc URL
        article_id = ArticleCrawler.get_meta(soup, name="tt_article_id")
        if article_id:
            return article_id
        match = re.search(r"/(\d+)\.html(?:$|\?)", url)
        return match.group(1) if match else None

    @staticmethod
    def extract_published_at(soup: BeautifulSoup, rss_metadata: dict) -> str | None:
        # Bóc tách thời gian xuất bản từ meta tags hoặc RSS
        candidates = [
            ArticleCrawler.get_meta(soup, name="pubdate"),
            ArticleCrawler.get_meta(soup, itemprop="datePublished"),
            ArticleCrawler.get_meta(soup, property="article:published_time"),
            rss_metadata.get("published_at"),
        ]
        for val in candidates:
            if val:
                return val
        return None

    def parse(self, html: str, url: str, rss_metadata: dict | None = None) -> dict:
        # Chuyển đổi mã nguồn HTML bài báo thành từ điển dữ liệu có cấu trúc
        soup = BeautifulSoup(html, "lxml")
        rss = rss_metadata or {}
        title = (
            self.normalize_text(soup.select_one("h1.title-detail"))
            or self.get_meta(soup, property="og:title")
            or self.normalize_text(soup.find("h1"))
            or rss.get("title")
        )
        description = (
            self.normalize_text(soup.select_one("p.description"))
            or self.get_meta(soup, property="og:description")
            or self.get_meta(soup, name="description")
            or rss.get("description")
        )
        return {
            "url": url,
            "title": title,
            "description": description,
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
        # Tải trang và phân tích một bài viết VnExpress
        return self.parse(html=self.fetch(url), url=url, rss_metadata=rss_metadata)