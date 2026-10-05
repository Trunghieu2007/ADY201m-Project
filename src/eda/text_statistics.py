from __future__ import annotations

import json
import re
import statistics
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT = PROJECT_ROOT / "data" / "raw" / "articles.jsonl"
OUTPUT = PROJECT_ROOT / "outputs" / "eda" / "text_statistics.json"


# Tải danh sách các bài báo từ tệp JSONL
def load_articles(path: Path = INPUT) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    articles: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at line {line_number}: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Line {line_number} is not a JSON object.")
            articles.append(record)
    return articles


# Lấy văn bản từ bản ghi hoặc chuỗi rỗng nếu không tồn tại
def get_text(record: dict[str, Any], field: str) -> str:
    val = record.get(field)
    return "" if val is None else str(val).strip()


# Tách từ theo khoảng trắng phục vụ thống kê mô tả
def tokenize(text: str) -> list[str]:
    return re.findall(r"\S+", str(text)) if text else []


# Trích xuất các từ chuẩn hóa chữ thường để đếm từ vựng độc nhất
def normalized_words(text: str) -> list[str]:
    return re.findall(r"[^\W_]+", str(text).casefold(), flags=re.UNICODE) if text else []


# Đếm số lượng từ trong văn bản
def word_count(text: str) -> int:
    return len(tokenize(text))


# Đếm tổng số ký tự trong chuỗi văn bản
def character_count(text: str) -> int:
    return len(text or "")


# Ước lượng số câu dựa trên các dấu chấm câu kết thúc
def sentence_count(text: str) -> int:
    if not text:
        return 0
    return sum(1 for part in re.split(r"[.!?…]+", str(text)) if part.strip())


# Đếm số lượng từ vựng độc nhất đã được chuẩn hóa
def unique_word_count(text: str) -> int:
    return len(set(normalized_words(text)))


# Tính độ dài ký tự trung bình của các từ
def average_word_length(text: str) -> float:
    words = normalized_words(text)
    return sum(len(w) for w in words) / len(words) if words else 0.0


# Tính toán các chỉ số thống kê mô tả tóm tắt (min, max, mean, median, std, q1, q3)
def describe(values: list[int | float]) -> dict[str, Any]:
    clean = sorted([v for v in values if v is not None and not isinstance(v, bool)])
    if not clean:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None, "std": None, "q1": None, "q3": None}
    if len(clean) >= 2:
        q1, _, q3 = statistics.quantiles(clean, n=4)
        std = statistics.stdev(clean)
    else:
        q1 = q3 = clean[0]
        std = 0.0
    return {
        "count": len(clean), "min": min(clean), "max": max(clean),
        "mean": round(statistics.mean(clean), 2), "median": round(statistics.median(clean), 2),
        "std": round(std, 2), "q1": round(q1, 2), "q3": round(q3, 2),
    }


# Phân tích tổng thể các chỉ số văn bản cho tập hợp các bài báo
def analyze_articles(articles: list[dict[str, Any]]) -> dict[str, Any]:
    records_detail: list[dict[str, Any]] = []
    for art in articles:
        content = get_text(art, "content")
        title = get_text(art, "title")
        desc = get_text(art, "description")
        records_detail.append({
            "article_id": art.get("article_id"),
            "category": art.get("category"),
            "subcategory": art.get("subcategory"),
            "character_count": character_count(content),
            "word_count": word_count(content),
            "sentence_count": sentence_count(content),
            "unique_word_count": unique_word_count(content),
            "average_word_length": round(average_word_length(content), 2),
            "title_character_count": character_count(title),
            "title_word_count": word_count(title),
            "description_character_count": character_count(desc),
            "description_word_count": word_count(desc),
        })
    fields = [
        "character_count", "word_count", "sentence_count", "unique_word_count",
        "average_word_length", "title_character_count", "title_word_count",
        "description_character_count", "description_word_count",
    ]
    summary = {f: describe([r[f] for r in records_detail]) for f in fields}
    return {
        "dataset": str(INPUT.relative_to(PROJECT_ROOT)),
        "records": len(records_detail),
        "summary": summary,
        "records_detail": records_detail,
    }


# Ghi kết quả phân tích thống kê văn bản ra tệp JSON
def save_result(result: dict[str, Any], path: Path = OUTPUT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


# Điểm thực thi chính phân tích văn bản
def main() -> dict[str, Any]:
    articles = load_articles()
    result = analyze_articles(articles)
    save_result(result)
    return result


if __name__ == "__main__":
    res = main()
    print(f"Text statistics complete: {res['records']} articles analyzed.")
