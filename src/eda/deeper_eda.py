"""Module phân tích khám phá chuyên sâu (Deeper EDA) và trực quan hóa xu hướng.
Phân tích ma trận quan hệ category x subcategory, phân bố độ dài văn bản theo chuyên mục,
và tự động kết xuất các biểu đồ trực quan hóa dữ liệu phục vụ báo cáo.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from src.utils import (
    OUTPUTS_DIR,
    RAW_DATA_PATH,
    describe_numeric,
    load_jsonl,
    save_json,
)
from .temporal_analysis import parse_datetime
from .text_statistics import get_text, word_count

EDA_DIR = OUTPUTS_DIR / "eda"
JSON_FILE = EDA_DIR / "deeper_eda.json"

CHART_CATEGORY_SUBCATEGORY = EDA_DIR / "category_subcategory.png"
CHART_AVERAGE_WORDS = EDA_DIR / "average_words_by_category.png"
CHART_PUBLICATION_HOUR = EDA_DIR / "publication_hour.png"
CHART_PUBLICATION_CRAWL_GAP = EDA_DIR / "publication_to_crawl_gap_by_category.png"
CHART_CONTENT_LENGTH = EDA_DIR / "content_length_distribution.png"
CHART_WORD_COUNT = EDA_DIR / "word_count_distribution.png"


def load_articles(path: Path = RAW_DATA_PATH) -> list[dict[str, Any]]:
    """Đọc danh sách bản ghi JSON từ file JSONL."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return load_jsonl(path)


def numeric_stats(values: list[float | int]) -> dict[str, Any]:
    """Tính toán 7 chỉ số thống kê cơ bản cho mảng giá trị số."""
    return describe_numeric(values)


def analyze_category_relationships(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """Phân tích quan hệ giữa danh mục chính và danh mục con."""
    cat_counter: Counter[str] = Counter()
    subcat_counter: Counter[str] = Counter()
    mapping: dict[str, Counter[str]] = defaultdict(Counter)
    pair_counter: Counter[tuple[str, str]] = Counter()

    for article in articles:
        category = get_text(article, "category") or "(missing)"
        subcategory = get_text(article, "subcategory") or "(missing)"
        cat_counter[category] += 1
        subcat_counter[subcategory] += 1
        mapping[category][subcategory] += 1
        pair_counter[(category, subcategory)] += 1

    return {
        "category_distribution": dict(sorted(cat_counter.items())),
        "subcategory_distribution": dict(sorted(subcat_counter.items())),
        "category_to_subcategory": {cat: dict(sorted(sub.items())) for cat, sub in sorted(mapping.items())},
        "category_subcategory_pairs": {f"{c} -> {s}": count for (c, s), count in sorted(pair_counter.items())},
    }


def analyze_text_by_category(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """Thống kê số lượng từ và ký tự phân theo từng danh mục."""
    grouped_words: dict[str, list[int]] = defaultdict(list)
    grouped_chars: dict[str, list[int]] = defaultdict(list)
    for article in articles:
        category = get_text(article, "category") or "(missing)"
        content = get_text(article, "content")
        grouped_words[category].append(word_count(content))
        grouped_chars[category].append(len(content))

    return {
        cat: {
            "articles": len(grouped_words[cat]),
            "word_count": numeric_stats(grouped_words[cat]),
            "content_length": numeric_stats(grouped_chars[cat]),
        }
        for cat in sorted(grouped_words)
    }


def analyze_metadata(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """Thống kê phân phối các trường metadata (tác giả, nguồn, tòa soạn)."""
    def count_field(field: str) -> Counter[str]:
        return Counter(val for val in (get_text(a, field) for a in articles) if val)

    authors = count_field("author")
    publishers = count_field("publisher")
    sources = count_field("source")
    article_ids = count_field("article_id")
    return {
        "unique_authors": len(authors), "author_distribution": dict(authors.most_common()),
        "unique_publishers": len(publishers), "publisher_distribution": dict(publishers.most_common()),
        "unique_sources": len(sources), "source_distribution": dict(sources.most_common()),
        "unique_article_ids": len(article_ids),
    }


def analyze_temporal_cross_tab(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """Phân tích bảng chéo ngày xuất bản x chuyên mục."""
    pub_by_cat: dict[str, Counter[str]] = defaultdict(Counter)
    hour_by_cat: dict[str, Counter[int]] = defaultdict(Counter)
    for a in articles:
        dt = parse_datetime(a.get("published_at"))
        cat = get_text(a, "category") or "(missing)"
        if dt:
            pub_by_cat[cat][dt.date().isoformat()] += 1
            hour_by_cat[cat][dt.hour] += 1
    return {
        "publication_date_by_category": {cat: dict(sorted(counts.items())) for cat, counts in sorted(pub_by_cat.items())},
        "publication_hour_by_category": {cat: {f"{h:02d}:00": counts[h] for h in sorted(counts)} for cat, counts in sorted(hour_by_cat.items())},
    }


def gap_by_category(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """Tính độ trễ thu thập trung bình theo từng chuyên mục."""
    grouped: dict[str, list[float]] = defaultdict(list)
    for a in articles:
        pub = parse_datetime(a.get("published_at"))
        crw = parse_datetime(a.get("crawled_at"))
        cat = get_text(a, "category") or "(missing)"
        if pub and crw:
            gap = (crw - pub).total_seconds() / 60.0
            grouped[cat].append(gap)
    return {cat: numeric_stats(vals) for cat, vals in sorted(grouped.items())}


def create_category_subcategory_chart(data: dict[str, Any]) -> None:
    """Vẽ biểu đồ cột phân bố category và subcategory."""
    labels, values = [], []
    for cat, subcats in data["category_to_subcategory"].items():
        for sub, count in subcats.items():
            labels.append(f"{cat}\n{sub}")
            values.append(count)
    if not values:
        return
    plt.figure(figsize=(12, 7))
    plt.bar(labels, values, color="#3498db")
    plt.title("Category and Subcategory Distribution", fontsize=14, fontweight="bold")
    plt.xlabel("Category / Subcategory")
    plt.ylabel("Number of articles")
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.tight_layout()
    plt.savefig(CHART_CATEGORY_SUBCATEGORY, dpi=150)
    plt.close()


def create_average_words_chart(data: dict[str, Any]) -> None:
    """Vẽ biểu đồ số lượng từ trung bình theo danh mục."""
    cats = list(data.keys())
    if not cats:
        return
    plt.figure(figsize=(10, 6))
    plt.bar(cats, [data[c]["word_count"]["mean"] for c in cats], color="#2ecc71")
    plt.title("Average Article Word Count by Category", fontsize=14, fontweight="bold")
    plt.xlabel("Category")
    plt.ylabel("Average words")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(CHART_AVERAGE_WORDS, dpi=150)
    plt.close()


def create_publication_hour_chart(data: dict[str, Any]) -> None:
    """Vẽ biểu đồ tần suất xuất bản theo các giờ trong ngày."""
    hours = sorted(int(h) for h in data["publication_hours"])
    if not hours:
        return
    plt.figure(figsize=(10, 6))
    plt.bar(hours, [data["publication_hours"][str(h)] for h in hours], color="#e74c3c")
    plt.title("Article Publication by Hour", fontsize=14, fontweight="bold")
    plt.xlabel("Hour of day")
    plt.ylabel("Number of articles")
    plt.xticks(range(24))
    plt.tight_layout()
    plt.savefig(CHART_PUBLICATION_HOUR, dpi=150)
    plt.close()


def create_gap_chart(data: dict[str, dict[str, Any]]) -> None:
    """Vẽ biểu đồ khoảng cách thời gian xuất bản đến crawl theo category."""
    cats = list(data.keys())
    if not cats:
        return
    plt.figure(figsize=(10, 6))
    plt.bar(cats, [data[c]["mean"] for c in cats], color="#9b59b6")
    plt.title("Average Publication-to-Crawl Gap by Category", fontsize=14, fontweight="bold")
    plt.xlabel("Category")
    plt.ylabel("Average timestamp gap (minutes)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(CHART_PUBLICATION_CRAWL_GAP, dpi=150)
    plt.close()


def create_distribution_chart(values: list[int], output: Path, title: str, xlabel: str, color: str = "#1abc9c") -> None:
    """Vẽ biểu đồ histogram phân phối tần suất của một mảng giá trị số."""
    clean = [v for v in values if v > 0]
    if not clean:
        return
    plt.figure(figsize=(10, 6))
    plt.hist(clean, bins=min(10, max(1, len(clean))), color=color, edgecolor="black")
    plt.title(title, fontsize=14, fontweight="bold")
    plt.xlabel(xlabel)
    plt.ylabel("Number of articles")
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    plt.close()


def analyze_articles(articles: list[dict[str, Any]], temporal_result: dict[str, Any]) -> dict[str, Any]:
    """Phân tích toàn diện bộ dữ liệu bài viết và kết hợp dữ liệu temporal."""
    cat_data = analyze_category_relationships(articles)
    text_data = analyze_text_by_category(articles)
    meta_data = analyze_metadata(articles)
    temporal_cross = analyze_temporal_cross_tab(articles)
    gap_cat = gap_by_category(articles)
    temporal_compatible = {
        "publication_dates": temporal_result["publication_date_distribution"],
        "publication_hours": temporal_result["publication_hour_distribution"],
        "publication_to_crawl_gap_minutes": temporal_result["publication_to_crawl_gap_minutes"],
    }
    return {
        "records": len(articles),
        "category_analysis": cat_data,
        "text_by_category": text_data,
        "temporal_analysis": temporal_compatible,
        "category_temporal_analysis": temporal_cross,
        "publication_to_crawl_gap_by_category": gap_cat,
        "metadata_analysis": meta_data,
    }


def save_outputs(report: dict[str, Any], articles: list[dict[str, Any]]) -> None:
    """Lưu trữ file kết quả JSON và kết xuất các biểu đồ trực quan."""
    EDA_DIR.mkdir(parents=True, exist_ok=True)
    save_json(JSON_FILE, report)
    create_category_subcategory_chart(report["category_analysis"])
    create_average_words_chart(report["text_by_category"])
    create_publication_hour_chart(report["temporal_analysis"])
    create_gap_chart(report["publication_to_crawl_gap_by_category"])
    create_distribution_chart([len(get_text(a, "content")) for a in articles], CHART_CONTENT_LENGTH, "Article Content Length Distribution", "Character count", color="#f39c12")
    create_distribution_chart([word_count(get_text(a, "content")) for a in articles], CHART_WORD_COUNT, "Article Word Count Distribution", "Approximate word/token count", color="#16a085")


def main() -> dict[str, Any]:
    """Khởi chạy quy trình Deeper EDA từ dòng lệnh."""
    articles = load_articles()
    from .temporal_analysis import analyze_articles as analyze_temporal_articles
    report = analyze_articles(articles, analyze_temporal_articles(articles))
    save_outputs(report, articles)
    return report


if __name__ == "__main__":
    main()
