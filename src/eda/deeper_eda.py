from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from .temporal_analysis import parse_datetime
from .text_statistics import get_text, word_count

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FILE = PROJECT_ROOT / "data" / "raw" / "articles.jsonl"
EDA_DIR = PROJECT_ROOT / "outputs" / "eda"
JSON_FILE = EDA_DIR / "deeper_eda.json"
SUMMARY_FILE = EDA_DIR / "deeper_eda_summary.txt"

CHART_CATEGORY_SUBCATEGORY = EDA_DIR / "category_subcategory.png"
CHART_AVERAGE_WORDS = EDA_DIR / "average_words_by_category.png"
CHART_PUBLICATION_HOUR = EDA_DIR / "publication_hour.png"
CHART_PUBLICATION_CRAWL_GAP = EDA_DIR / "publication_to_crawl_gap_by_category.png"
CHART_CONTENT_LENGTH = EDA_DIR / "content_length_distribution.png"
CHART_WORD_COUNT = EDA_DIR / "word_count_distribution.png"


# Đọc danh sách bản ghi JSON từ file JSONL
def load_articles(path: Path = RAW_FILE) -> list[dict[str, Any]]:
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


# Tính toán các chỉ số thống kê cơ bản cho mảng giá trị số
def numeric_stats(values: list[float | int]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None, "std": None, "q1": None, "q3": None}
    values = sorted(values)
    if len(values) >= 2:
        q1, _, q3 = statistics.quantiles(values, n=4)
        std = statistics.stdev(values)
    else:
        q1 = q3 = values[0]
        std = 0.0
    return {
        "count": len(values), "min": round(min(values), 2), "max": round(max(values), 2),
        "mean": round(statistics.mean(values), 2), "median": round(statistics.median(values), 2),
        "std": round(std, 2), "q1": round(q1, 2), "q3": round(q3, 2),
    }


# Phân tích quan hệ giữa danh mục chính và danh mục con
def analyze_category_relationships(articles: list[dict[str, Any]]) -> dict[str, Any]:
    cat_counter, subcat_counter = Counter(), Counter()
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


# Thống kê số lượng từ và ký tự phân theo từng danh mục
def analyze_text_by_category(articles: list[dict[str, Any]]) -> dict[str, Any]:
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


# Thống kê phân phối các trường metadata (tác giả, nguồn, tòa soạn)
def analyze_metadata(articles: list[dict[str, Any]]) -> dict[str, Any]:
    def count_field(field: str) -> Counter[str]:
        return Counter(val for val in (get_text(a, field) for a in articles) if val)

    authors, publishers = count_field("author"), count_field("publisher")
    sources, article_ids = count_field("source"), count_field("article_id")
    return {
        "unique_authors": len(authors), "author_distribution": dict(authors.most_common()),
        "unique_publishers": len(publishers), "publisher_distribution": dict(publishers.most_common()),
        "unique_sources": len(sources), "source_distribution": dict(sources.most_common()),
        "unique_article_ids": len(article_ids),
    }


# Bảng chéo theo dõi tần suất xuất bản theo ngày và danh mục
def analyze_temporal_cross_tab(articles: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Counter[str]] = defaultdict(Counter)
    for article in articles:
        dt = parse_datetime(article.get("published_at"))
        if dt:
            result[dt.date().isoformat()][get_text(article, "category") or "(missing)"] += 1
    return {date: dict(sorted(cats.items())) for date, cats in sorted(result.items())}


# Tính toán khoảng cách phút giữa thời gian xuất bản và thời gian crawl
def calculate_gap_minutes(article: dict[str, Any]) -> float | None:
    pub, crw = parse_datetime(article.get("published_at")), parse_datetime(article.get("crawled_at"))
    if not pub or not crw or (pub.tzinfo is None) != (crw.tzinfo is None):
        return None
    return (crw - pub).total_seconds() / 60.0


# Thống kê khoảng cách thời gian xuất bản đến crawl theo từng danh mục
def gap_by_category(articles: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for article in articles:
        gap = calculate_gap_minutes(article)
        if gap is not None:
            grouped[get_text(article, "category") or "(missing)"].append(gap)
    return {cat: numeric_stats(vals) for cat, vals in sorted(grouped.items())}


# Tự động rút ra các phát hiện nổi bật từ kết quả EDA
def generate_findings(
    articles: list[dict[str, Any]], category_data: dict[str, Any],
    text_data: dict[str, Any], temporal_data: dict[str, Any], metadata_data: dict[str, Any],
) -> list[str]:
    findings: list[str] = []
    n = len(articles)
    counts = list(category_data["category_distribution"].values())
    if counts and len(set(counts)) == 1:
        findings.append("The current sample is evenly distributed across its sampled categories.")
    elif counts:
        findings.append("The current sample does not contain an equal number of articles in every category.")

    findings.append(f"The {n}-article sample contains {len(category_data['subcategory_distribution'])} distinct subcategories.")
    if text_data:
        largest = max(text_data, key=lambda c: text_data[c]["word_count"]["mean"])
        smallest = min(text_data, key=lambda c: text_data[c]["word_count"]["mean"])
        findings.append(
            f"Among sampled categories, '{largest}' has the highest mean article word count "
            f"({text_data[largest]['word_count']['mean']}), while '{smallest}' has the lowest ({text_data[smallest]['word_count']['mean']})."
        )
    dates = temporal_data["publication_dates"]
    if dates:
        busiest_date = max(dates, key=dates.get)
        findings.append(f"The sample spans {len(dates)} publication date(s); {busiest_date} has the largest sampled count ({dates[busiest_date]} articles).")
    hours = temporal_data["publication_hours"]
    if hours:
        busiest_hour = max(hours, key=lambda h: hours[h])
        findings.append(f"Within this sample, {busiest_hour}:00 is the most frequent publication hour ({hours[busiest_hour]} articles).")
    gap = temporal_data["publication_to_crawl_gap_minutes"]
    if gap["count"] > 0:
        findings.append(f"The observed publication-to-crawl timestamp gap has a mean of {gap['mean']} minutes and a median of {gap['median']} minutes.")

    findings.append(f"The sample contains {metadata_data['unique_authors']} distinct author value(s).")
    if len(metadata_data["publisher_distribution"]) == 1:
        findings.append(f"All sampled records use the same publisher value: '{next(iter(metadata_data['publisher_distribution']))}'.")
    if len(metadata_data["source_distribution"]) == 1:
        findings.append(f"All sampled records use the same source value: '{next(iter(metadata_data['source_distribution']))}'.")
    findings.append(f"All findings describe only the current {n}-article sample and should not be generalized to the full VnExpress corpus.")
    return findings


# Vẽ biểu đồ cột phân bố category và subcategory
def create_category_subcategory_chart(data: dict[str, Any]) -> None:
    labels, values = [], []
    for cat, subcats in data["category_to_subcategory"].items():
        for sub, count in subcats.items():
            labels.append(f"{cat}\n{sub}")
            values.append(count)
    if not values:
        return
    plt.figure(figsize=(12, 7))
    plt.bar(labels, values)
    plt.title("Category and Subcategory Distribution")
    plt.xlabel("Category / Subcategory")
    plt.ylabel("Number of articles")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(CHART_CATEGORY_SUBCATEGORY, dpi=150)
    plt.close()


# Vẽ biểu đồ số lượng từ trung bình theo danh mục
def create_average_words_chart(data: dict[str, Any]) -> None:
    cats = list(data.keys())
    if not cats:
        return
    plt.figure(figsize=(10, 6))
    plt.bar(cats, [data[c]["word_count"]["mean"] for c in cats])
    plt.title("Average Article Word Count by Category")
    plt.xlabel("Category")
    plt.ylabel("Average words")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(CHART_AVERAGE_WORDS, dpi=150)
    plt.close()


# Vẽ biểu đồ tần suất xuất bản theo các giờ trong ngày
def create_publication_hour_chart(data: dict[str, Any]) -> None:
    hours = sorted(int(h) for h in data["publication_hours"])
    if not hours:
        return
    plt.figure(figsize=(10, 6))
    plt.bar(hours, [data["publication_hours"][str(h)] for h in hours])
    plt.title("Article Publication by Hour")
    plt.xlabel("Hour of day")
    plt.ylabel("Number of articles")
    plt.xticks(range(24))
    plt.tight_layout()
    plt.savefig(CHART_PUBLICATION_HOUR, dpi=150)
    plt.close()


# Vẽ biểu đồ khoảng cách thời gian xuất bản đến crawl theo category
def create_gap_chart(data: dict[str, dict[str, Any]]) -> None:
    cats = list(data.keys())
    if not cats:
        return
    plt.figure(figsize=(10, 6))
    plt.bar(cats, [data[c]["mean"] for c in cats])
    plt.title("Average Publication-to-Crawl Gap by Category")
    plt.xlabel("Category")
    plt.ylabel("Average timestamp gap (minutes)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(CHART_PUBLICATION_CRAWL_GAP, dpi=150)
    plt.close()


# Vẽ biểu đồ histogram phân phối tần suất của một mảng giá trị số
def create_distribution_chart(values: list[int], output: Path, title: str, xlabel: str) -> None:
    clean = [v for v in values if v > 0]
    if not clean:
        return
    plt.figure(figsize=(10, 6))
    plt.hist(clean, bins=min(10, max(1, len(clean))))
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Number of articles")
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    plt.close()


# Biên soạn báo cáo tổng hợp chi tiết dạng Markdown/văn bản
def build_summary(report: dict[str, Any]) -> str:
    lines = ["ADY201m - DEEPER EDA", "=" * 70, "", "1. CATEGORY / SUBCATEGORY", "-" * 70]
    for cat, subcats in report["category_analysis"]["category_to_subcategory"].items():
        lines.append(f"{cat}:")
        for sub, count in subcats.items():
            lines.append(f"  - {sub}: {count}")
    lines.extend(["", "2. TEXT STATISTICS BY CATEGORY", "-" * 70])
    for cat, data in report["text_by_category"].items():
        w, c = data["word_count"], data["content_length"]
        lines.extend([
            f"{cat}:", f"  Articles: {data['articles']}", f"  Mean words: {w['mean']}",
            f"  Median words: {w['median']}", f"  Min words: {w['min']}", f"  Max words: {w['max']}",
            f"  Mean chars: {c['mean']}", f"  Median chars: {c['median']}", "",
        ])
    temp = report["temporal_analysis"]
    lines.extend(["3. TEMPORAL ANALYSIS", "-" * 70, "Publication dates:"])
    for d, cnt in temp["publication_dates"].items():
        lines.append(f"  - {d}: {cnt}")
    lines.extend(["", "Publication hours:"])
    for h, cnt in temp["publication_hours"].items():
        lines.append(f"  - {int(h):02d}:00: {cnt}")
    gap = temp["publication_to_crawl_gap_minutes"]
    lines.extend([
        "", "Publication-to-crawl timestamp gap:",
        f"  Min:    {gap['min']} minutes", f"  Max:    {gap['max']} minutes",
        f"  Mean:   {gap['mean']} minutes", f"  Median: {gap['median']} minutes",
        "", "4. METADATA", "-" * 70,
        f"Unique authors: {report['metadata_analysis']['unique_authors']}",
        f"Unique publishers: {report['metadata_analysis']['unique_publishers']}",
        f"Unique sources: {report['metadata_analysis']['unique_sources']}",
        f"Unique article IDs: {report['metadata_analysis']['unique_article_ids']}",
        "", "5. EDA FINDINGS", "-" * 70,
    ])
    for idx, f in enumerate(report["findings"], start=1):
        lines.append(f"{idx}. {f}")
    lines.extend([
        "", "IMPORTANT:",
        "  This analysis is descriptive only.",
        "  It reads the raw dataset and does not modify it.",
        "  Word count uses whitespace-based tokens; sentence count is approximate.",
        "  Publication-to-crawl gap is a timestamp difference, not crawler execution latency.",
    ])
    return "\n".join(lines)


# Phân tích toàn diện bộ dữ liệu bài viết và kết hợp dữ liệu temporal
def analyze_articles(articles: list[dict[str, Any]], temporal_result: dict[str, Any]) -> dict[str, Any]:
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
    findings = generate_findings(articles, cat_data, text_data, temporal_compatible, meta_data)
    return {
        "dataset": str(RAW_FILE.relative_to(PROJECT_ROOT)), "records": len(articles),
        "category_analysis": cat_data, "text_by_category": text_data,
        "temporal_analysis": temporal_compatible, "category_temporal_analysis": temporal_cross,
        "publication_to_crawl_gap_by_category": gap_cat, "metadata_analysis": meta_data,
        "findings": findings,
        "limitations": [
            "Current dataset contains only 20 articles.",
            "Statistics are descriptive and apply only to this dataset.",
            "Results should not be generalized to the entire VnExpress corpus.",
            "Word counts use simple whitespace tokenization.",
            "Sentence counts are approximate.",
            "Publication-to-crawl gap depends on the semantics of the stored timestamps.",
        ],
    }


# Lưu trữ các file kết quả JSON, TXT và toàn bộ biểu đồ EDA
def save_outputs(report: dict[str, Any], articles: list[dict[str, Any]]) -> None:
    EDA_DIR.mkdir(parents=True, exist_ok=True)
    JSON_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_FILE.write_text(build_summary(report), encoding="utf-8")
    create_category_subcategory_chart(report["category_analysis"])
    create_average_words_chart(report["text_by_category"])
    create_publication_hour_chart(report["temporal_analysis"])
    create_gap_chart(report["publication_to_crawl_gap_by_category"])
    create_distribution_chart([len(get_text(a, "content")) for a in articles], CHART_CONTENT_LENGTH, "Article Content Length Distribution", "Character count")
    create_distribution_chart([word_count(get_text(a, "content")) for a in articles], CHART_WORD_COUNT, "Article Word Count Distribution", "Approximate word/token count")


# Điểm khởi chạy chính cho module Deeper EDA
def main() -> dict[str, Any]:
    articles = load_articles()
    from .temporal_analysis import analyze_articles as analyze_temporal_articles
    report = analyze_articles(articles, analyze_temporal_articles(articles))
    save_outputs(report, articles)
    return report


if __name__ == "__main__":
    report = main()
    print("=" * 70 + "\nDEEPER EDA COMPLETE\n" + "=" * 70)
    print(f"Records: {report['records']}\nCategories: {len(report['category_analysis']['category_distribution'])}")
    print(f"Subcategories: {len(report['category_analysis']['subcategory_distribution'])}")
    print(f"Unique authors: {report['metadata_analysis']['unique_authors']}\nJSON report: {JSON_FILE}\nTXT report: {SUMMARY_FILE}")
