from __future__ import annotations

import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT = PROJECT_ROOT / "data" / "raw" / "articles.jsonl"
OUTPUT = PROJECT_ROOT / "outputs" / "eda" / "temporal_analysis.json"


# Tải danh sách bài báo từ tệp JSONL
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


# Chuyển đổi chuỗi thời gian nhiều định dạng sang đối tượng datetime
def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


# Tính chênh lệch thời gian giữa thời điểm cào và xuất bản (đơn vị phút)
def comparable_gap_minutes(published: datetime, crawled: datetime) -> float | None:
    if (published.tzinfo is None) != (crawled.tzinfo is None):
        return None
    return (crawled - published).total_seconds() / 60.0


# Thống kê phân bố chuỗi số (min, max, mean, median, std, q1, q3)
def describe(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None, "std": None, "q1": None, "q3": None}
    vals = sorted(values)
    if len(vals) >= 2:
        q1, _, q3 = statistics.quantiles(vals, n=4)
        std = statistics.stdev(vals)
    else:
        q1 = q3 = vals[0]
        std = 0.0
    return {
        "count": len(vals), "min": round(min(vals), 2), "max": round(max(vals), 2),
        "mean": round(statistics.mean(vals), 2), "median": round(statistics.median(vals), 2),
        "std": round(std, 2), "q1": round(q1, 2), "q3": round(q3, 2),
    }


# Phân tích chuỗi thời gian xuất bản và độ trễ thu thập dữ liệu
def analyze_articles(articles: list[dict[str, Any]]) -> dict[str, Any]:
    date_dist: dict[str, int] = {}
    hour_dist: dict[str, int] = {}
    pub_cat: dict[str, dict[str, int]] = {}
    invalid_pub: list[Any] = []
    invalid_crawl: list[Any] = []
    incomparable_ids: list[Any] = []
    negative_ids: list[Any] = []
    gaps: list[float] = []

    for art in articles:
        aid = art.get("article_id")
        pub = parse_datetime(art.get("published_at"))
        crw = parse_datetime(art.get("crawled_at"))
        cat = str(art.get("category") or "(missing)")

        if pub is None:
            invalid_pub.append(aid)
        else:
            d_key = pub.date().isoformat()
            h_key = str(pub.hour)
            date_dist[d_key] = date_dist.get(d_key, 0) + 1
            hour_dist[h_key] = hour_dist.get(h_key, 0) + 1
            if d_key not in pub_cat:
                pub_cat[d_key] = {}
            pub_cat[d_key][cat] = pub_cat[d_key].get(cat, 0) + 1

        if crw is None:
            invalid_crawl.append(aid)

        if pub is not None and crw is not None:
            gap = comparable_gap_minutes(pub, crw)
            if gap is None:
                incomparable_ids.append(aid)
            else:
                gaps.append(gap)
                if gap < 0:
                    negative_ids.append(aid)

    return {
        "records": len(articles),
        "published_at": {"valid": len(articles) - len(invalid_pub), "invalid": len(invalid_pub), "invalid_article_ids": invalid_pub},
        "crawled_at": {"valid": len(articles) - len(invalid_crawl), "invalid": len(invalid_crawl), "invalid_article_ids": invalid_crawl},
        "publication_date_distribution": dict(sorted(date_dist.items())),
        "publication_hour_distribution": dict(sorted(hour_dist.items(), key=lambda item: int(item[0]))),
        "publication_by_date_and_category": {d: dict(sorted(cats.items())) for d, cats in sorted(pub_cat.items())},
        "publication_to_crawl_gap_minutes": {
            **describe(gaps),
            "values": [round(v, 2) for v in gaps],
            "negative_gap_count": len(negative_ids),
            "negative_gap_article_ids": negative_ids,
            "incomparable_timezone_count": len(incomparable_ids),
            "incomparable_timezone_article_ids": incomparable_ids,
        },
        "interpretation_note": "Observed timestamp gap between crawl time and published time.",
    }


# Ghi kết quả phân tích thời gian ra tệp JSON
def save_result(result: dict[str, Any], path: Path = OUTPUT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


# Điểm thực thi chính phân tích thời gian
def main() -> dict[str, Any]:
    articles = load_articles()
    result = analyze_articles(articles)
    save_result(result)
    return result


if __name__ == "__main__":
    main()
