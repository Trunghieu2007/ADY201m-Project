"""Module tiện ích dùng chung cho toàn bộ dự án ADY201m.
Chứa các hằng số cấu hình hệ thống, hàm xử lý tệp JSON/JSONL, tính mã băm SHA-256
và các hàm thống kê mô tả cơ bản tuân thủ chuẩn tri thức Knowledge.md.
"""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path
from typing import Any

# Tự động cấu hình terminal Windows hiển thị tiếng Việt UTF-8 không bị lỗi font
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Định nghĩa các đường dẫn thư mục và tệp cốt lõi của dự án
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "articles.jsonl"
CRAWL_LOG_PATH = DATA_DIR / "raw" / "crawl_log.jsonl"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "articles_processed.jsonl"
CATEGORY_SUMMARY_PATH = DATA_DIR / "processed" / "category_summary.json"
FEATURE_MATRIX_PATH = DATA_DIR / "processed" / "feature_matrix.csv"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
SQL_DIR = PROJECT_ROOT / "sql"

# Danh sách 12 trường cấu trúc bắt buộc của bản ghi tin tức thô
EXPECTED_FIELDS = [
    "url", "title", "description", "content", "author", "publisher",
    "published_at", "category", "subcategory", "article_id", "crawled_at", "source",
]

# Các trường bắt buộc không được phép rỗng
NONEMPTY_FIELDS = [
    "url", "title", "description", "content", "publisher",
    "published_at", "category", "crawled_at", "source",
]

# 5 chuyên mục tin tức mục tiêu của đồ án
TARGET_CATEGORIES = [
    "Thời sự", "Kinh doanh", "Bất động sản", "Khoa học công nghệ", "Sức khỏe",
]

# Bảng ánh xạ slug URL sang tên tiếng Việt chuẩn hóa
CANONICAL_CATEGORIES = {
    "thoi-su": "Thời sự",
    "kinh-doanh": "Kinh doanh",
    "bat-dong-san": "Bất động sản",
    "khoa-hoc": "Khoa học công nghệ",
    "khoa-hoc-cong-nghe": "Khoa học công nghệ",
    "suc-khoe": "Sức khỏe",
}

# 13 đặc trưng mô tả cho bảng ArticleFeatures
FEATURE_COLUMNS = (
    "char_count", "word_count", "sentence_count", "unique_word_count",
    "lexical_diversity", "avg_word_length", "title_char_count", "title_word_count",
    "description_char_count", "description_word_count", "title_to_content_word_ratio",
    "publication_hour", "publication_weekday",
)

# Tập từ dừng (stopwords) tiếng Việt phổ biến cho lọc từ khóa tần suất
STOPWORDS = {
    "và", "của", "là", "có", "cho", "trong", "được", "các", "với", "những",
    "đã", "khi", "người", "đến", "ở", "này", "về", "một", "để", "ra",
    "sau", "từ", "theo", "nhiều", "hơn", "không", "sẽ", "như", "lại", "vào",
    "cũng", "đang", "tại", "biết", "lên", "trên", "phải", "ngày", "bị", "rồi",
    "rất", "nói", "hay", "còn", "thì", "làm", "nhưng", "qua", "do", "gần",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Đọc dữ liệu từ tệp JSON Lines (JSONL).
    Mỗi dòng là một đối tượng JSON hợp lệ, bỏ qua các dòng trống.
    """
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_num, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if isinstance(record, dict):
                    records.append(record)
            except json.JSONDecodeError as exc:
                print(f"[Cảnh báo] Lỗi cú pháp JSON tại dòng {line_num} trong {path}: {exc}")
    return records


def save_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    """Ghi danh sách bản ghi ra tệp JSON Lines theo chuẩn mã hóa UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    """Đọc tệp JSON và trả về từ điển dữ liệu (dict)."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data: Any, indent: int = 2) -> None:
    """Ghi đối tượng dữ liệu ra tệp JSON định dạng có thụt lề chuẩn UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=indent)


def calculate_sha256(path: Path) -> str:
    """Tính toán mã băm SHA-256 của tệp để kiểm định tính bất biến của dữ liệu gốc."""
    if not path.exists():
        return ""
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def describe_numeric(values: list[float | int]) -> dict[str, Any]:
    """Tính toán 7 chỉ số thống kê mô tả (min, max, mean, median, std, q1, q3).
    Tuân thủ đúng định hướng môn học ADY201m (Descriptive Statistics).
    """
    clean = sorted([v for v in values if v is not None and not isinstance(v, bool)])
    if not clean:
        return {
            "count": 0, "min": None, "max": None, "mean": None,
            "median": None, "std": None, "q1": None, "q3": None,
        }
    if len(clean) >= 2:
        q1, _, q3 = statistics.quantiles(clean, n=4)
        std = statistics.stdev(clean)
    else:
        q1 = q3 = clean[0]
        std = 0.0
    return {
        "count": len(clean),
        "min": round(min(clean), 2),
        "max": round(max(clean), 2),
        "mean": round(statistics.mean(clean), 2),
        "median": round(statistics.median(clean), 2),
        "std": round(std, 2),
        "q1": round(q1, 2),
        "q3": round(q3, 2),
    }
