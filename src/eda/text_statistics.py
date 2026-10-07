"""Module thống kê từ vựng và đặc trưng văn bản cho phân tích EDA (Phase EDA - Text Statistics).
Tính toán độ dài văn bản (ký tự, từ, câu), độ đa dạng từ vựng và tóm tắt thống kê mô tả.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.utils import (
    OUTPUTS_DIR,
    RAW_DATA_PATH,
    describe_numeric,
    load_jsonl,
    save_json,
)

INPUT = RAW_DATA_PATH
OUTPUT = OUTPUTS_DIR / "eda" / "text_statistics.json"


def load_articles(path: Path = INPUT) -> list[dict[str, Any]]:
    """Tải danh sách các bài báo từ tệp JSONL."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return load_jsonl(path)


def get_text(record: dict[str, Any], field: str) -> str:
    """Lấy văn bản từ bản ghi hoặc chuỗi rỗng nếu không tồn tại."""
    val = record.get(field)
    return "" if val is None else str(val).strip()


def tokenize(text: str) -> list[str]:
    """Tách từ theo khoảng trắng phục vụ thống kê mô tả."""
    return re.findall(r"\S+", str(text)) if text else []


def normalized_words(text: str) -> list[str]:
    """Trích xuất các từ chuẩn hóa chữ thường để đếm từ vựng độc nhất."""
    return re.findall(r"[^\W_]+", str(text).casefold(), flags=re.UNICODE) if text else []


def word_count(text: str) -> int:
    """Đếm số lượng từ trong văn bản."""
    return len(tokenize(text))


def character_count(text: str) -> int:
    """Đếm tổng số ký tự trong chuỗi văn bản."""
    return len(text or "")


def sentence_count(text: str) -> int:
    """Ước lượng số câu dựa trên các dấu chấm câu kết thúc (. ! ? …)."""
    if not text:
        return 0
    return sum(1 for part in re.split(r"[.!?…]+", str(text)) if part.strip())


def unique_word_count(text: str) -> int:
    """Đếm số lượng từ vựng độc nhất đã được chuẩn hóa."""
    return len(set(normalized_words(text)))


def average_word_length(text: str) -> float:
    """Tính độ dài ký tự trung bình của các từ trong văn bản."""
    words = normalized_words(text)
    return sum(len(w) for w in words) / len(words) if words else 0.0


def describe(values: list[int | float]) -> dict[str, Any]:
    """Tính toán 7 chỉ số thống kê mô tả tóm tắt (min, max, mean, median, std, q1, q3)."""
    return describe_numeric(values)


def analyze_articles(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """Phân tích tổng thể các chỉ số văn bản cho tập hợp các bài báo."""
    records_detail: list[dict[str, Any]] = []
    for art in articles:
        content = get_text(art, "content")
        title = get_text(art, "title")
        description = get_text(art, "description")
        records_detail.append({
            "article_id": art.get("article_id"),
            "category": art.get("category"),
            "content_char_count": character_count(content),
            "content_word_count": word_count(content),
            "content_sentence_count": sentence_count(content),
            "content_unique_word_count": unique_word_count(content),
            "content_avg_word_length": average_word_length(content),
            "title_word_count": word_count(title),
            "description_word_count": word_count(description),
        })

    summary = {
        "content_char_count": describe([r["content_char_count"] for r in records_detail]),
        "content_word_count": describe([r["content_word_count"] for r in records_detail]),
        "content_sentence_count": describe([r["content_sentence_count"] for r in records_detail]),
        "content_unique_word_count": describe([r["content_unique_word_count"] for r in records_detail]),
        "content_avg_word_length": describe([r["content_avg_word_length"] for r in records_detail]),
        "title_word_count": describe([r["title_word_count"] for r in records_detail]),
        "description_word_count": describe([r["description_word_count"] for r in records_detail]),
    }

    result = {
        "records": len(articles),
        "summary": summary,
        "detail": records_detail,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    save_json(OUTPUT, result)
    return result


def save_result(result: dict[str, Any], path: Path = OUTPUT) -> None:
    """Ghi kết quả phân tích thống kê từ vựng ra tệp JSON."""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    save_json(path, result)


def main() -> None:
    """Khởi chạy phân tích thống kê từ vựng từ dòng lệnh."""
    articles = load_articles()
    res = analyze_articles(articles)
    print(f"Hoàn thành phân tích từ vựng cho {res['records']} bài báo. Kết quả lưu tại: {OUTPUT}")


if __name__ == "__main__":
    main()
