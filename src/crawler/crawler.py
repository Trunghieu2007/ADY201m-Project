from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from .article import ArticleCrawler
from .config import ARTICLE_OUTPUT, CRAWL_LOG_OUTPUT, MAX_ARTICLES, RAW_DATA_DIR, REQUEST_DELAY, RSS_FEEDS
from .rss import RSSCrawler

logger = logging.getLogger(__name__)


def save_jsonl(path: Path, record: dict) -> None:
    # Ghi nối tiếp một bản ghi dạng JSON vào tệp JSONL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_crawled_urls(path: Path) -> set[str]:
    # Đọc tập hợp các URL đã được cào từ tệp articles.jsonl để tránh trùng lặp
    if not path.exists():
        return set()
    urls: set[str] = set()
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                url = record.get("url")
                if url:
                    urls.add(url)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON at line %d in %s", line_number, path)
    return urls


def select_balanced_articles(articles: list[dict], max_articles: int, articles_per_category: int) -> list[dict]:
    # Lấy mẫu cân bằng số lượng bài báo cho từng chuyên mục
    grouped: dict[str, list[dict]] = defaultdict(list)
    for article in articles:
        category = article.get("category")
        if category:
            grouped[category].append(article)
    selected: list[dict] = []
    for category, _feed_url in RSS_FEEDS.values():
        selected.extend(grouped.get(category, [])[:articles_per_category])
    return selected[:max_articles]


def main() -> None:
    # Điều phối toàn bộ quy trình cào dữ liệu VnExpress từ RSS
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    rss_crawler = RSSCrawler()
    article_crawler = ArticleCrawler()

    logger.info("Starting VnExpress RSS discovery...")
    discovered = rss_crawler.discover()
    logger.info("Total articles discovered: %d", len(discovered))

    crawled_urls = load_crawled_urls(ARTICLE_OUTPUT)
    pending = [a for a in discovered if a["url"] not in crawled_urls]
    logger.info("Previously crawled: %d | New available: %d", len(crawled_urls), len(pending))

    selected = select_balanced_articles(pending, MAX_ARTICLES, articles_per_category=4)
    logger.info("Articles selected for this run: %d", len(selected))

    success_count = 0
    failure_count = 0
    for idx, rss_meta in enumerate(selected, start=1):
        url = rss_meta["url"]
        logger.info("[%d/%d] Crawling: %s", idx, len(selected), url)
        try:
            article = article_crawler.crawl(url=url, rss_metadata=rss_meta)
            save_jsonl(ARTICLE_OUTPUT, article)
            save_jsonl(CRAWL_LOG_OUTPUT, {"url": url, "status": "success", "timestamp": datetime.now(timezone.utc).isoformat()})
            success_count += 1
        except Exception as exc:
            failure_count += 1
            logger.exception("Failed to crawl: %s", url)
            save_jsonl(CRAWL_LOG_OUTPUT, {"url": url, "status": "failed", "error": str(exc), "timestamp": datetime.now(timezone.utc).isoformat()})
        time.sleep(REQUEST_DELAY)

    logger.info("Crawl finished. Success: %d | Failed: %d", success_count, failure_count)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()