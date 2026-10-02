from pathlib import Path

# Cấu hình đường dẫn dự án
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
ARTICLE_OUTPUT = RAW_DATA_DIR / "articles.jsonl"
CRAWL_LOG_OUTPUT = RAW_DATA_DIR / "crawl_log.jsonl"

# Nguồn cấp dữ liệu VnExpress
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

# Tham số vận hành crawler
REQUEST_TIMEOUT = 20
REQUEST_DELAY = 1.0
REQUEST_RETRIES = 3
REQUEST_RETRY_BACKOFF = 1.0
MAX_ARTICLES = 20
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/154.0.0.0 Safari/537.36 VnExpressDataScienceCrawler/0.1"
)

CATEGORIES = {key: label for key, (label, _url) in RSS_FEEDS.items()}
