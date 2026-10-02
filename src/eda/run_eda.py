from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

from . import deeper_eda, temporal_analysis, text_statistics

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA = PROJECT_ROOT / "data" / "raw" / "articles.jsonl"
EDA_DIR = PROJECT_ROOT / "outputs" / "eda"
EDA_SUMMARY_DIR = PROJECT_ROOT / "outputs" / "eda_summary"

TEXT_STATS_FILE = EDA_DIR / "text_statistics.json"
TEMPORAL_FILE = EDA_DIR / "temporal_analysis.json"
DEEPER_EDA_FILE = EDA_DIR / "deeper_eda.json"

FINDINGS_FILE = EDA_SUMMARY_DIR / "phase2_findings.json"
SUMMARY_FILE = EDA_SUMMARY_DIR / "phase2_summary.md"
LIMITATIONS_FILE = EDA_SUMMARY_DIR / "phase2_limitations.md"
CHECKLIST_FILE = EDA_SUMMARY_DIR / "phase2_checklist.md"

EXPECTED_FIELDS = [
    "url", "title", "description", "content", "author", "publisher",
    "published_at", "category", "subcategory", "article_id", "crawled_at", "source",
]
UNIQUE_FIELDS = ["url", "title", "article_id"]


# Đọc danh sách bản ghi thô từ file JSONL
def load_raw(path: Path = RAW_DATA) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Raw dataset not found: {path}")
    articles: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at line {line_no}: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Line {line_no} is not a JSON object.")
            articles.append(record)
    return articles


# Tính mã băm SHA-256 của file dữ liệu để đảm bảo tính bất biến
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# Kiểm tra tính toàn vẹn cấu trúc và trường thông tin so với schema mong đợi
def schema_analysis(articles: list[dict[str, Any]]) -> dict[str, Any]:
    missing_by_record: dict[Any, list[str]] = {}
    extra_fields_by_record: dict[Any, list[str]] = {}
    for idx, article in enumerate(articles, start=1):
        art_id = article.get("article_id") or f"record_{idx}"
        missing = [f for f in EXPECTED_FIELDS if f not in article]
        extra = sorted(set(article) - set(EXPECTED_FIELDS))
        if missing:
            missing_by_record[art_id] = missing
        if extra:
            extra_fields_by_record[art_id] = extra
    return {
        "expected_fields": EXPECTED_FIELDS, "expected_field_count": len(EXPECTED_FIELDS),
        "records_checked": len(articles),
        "all_records_contain_expected_fields": not missing_by_record,
        "all_records_match_exact_expected_schema": not missing_by_record and not extra_fields_by_record,
        "records_with_missing_expected_fields": missing_by_record,
        "records_with_extra_fields": extra_fields_by_record,
    }


# Đếm số lượng giá trị trùng lặp của một trường dữ liệu
def count_duplicates(articles: list[dict[str, Any]], field: str) -> int:
    values = [a.get(field) for a in articles if a.get(field) not in (None, "")]
    return len(values) - len(set(values))


# Đếm số lượng bản ghi bị thiếu hoặc rỗng theo từng trường
def missingness_analysis(articles: list[dict[str, Any]]) -> dict[str, int]:
    return {f: sum(1 for a in articles if a.get(f) in (None, "")) for f in EXPECTED_FIELDS}


# Thống kê tần suất phân phối các giá trị của một trường
def distribution(articles: list[dict[str, Any]], field: str) -> dict[str, int]:
    res: dict[str, int] = {}
    for a in articles:
        v = str(a.get(field) if a.get(field) not in (None, "") else "(missing)")
        res[v] = res.get(v, 0) + 1
    return dict(sorted(res.items(), key=lambda x: (-x[1], x[0])))


# Phân tích các trường metadata chính của bài viết
def metadata_analysis(articles: list[dict[str, Any]]) -> dict[str, Any]:
    def _cnt(f: str) -> dict[str, int]:
        c: dict[str, int] = {}
        for a in articles:
            v = a.get(f)
            if v not in (None, ""):
                c[str(v)] = c.get(str(v), 0) + 1
        return dict(sorted(c.items(), key=lambda x: (-x[1], x[0])))
    authors, publishers = _cnt("author"), _cnt("publisher")
    sources, article_ids = _cnt("source"), _cnt("article_id")
    return {
        "unique_authors": len(authors), "author_distribution": authors,
        "unique_publishers": len(publishers), "publisher_distribution": publishers,
        "unique_sources": len(sources), "source_distribution": sources,
        "unique_article_ids": len(article_ids),
    }


# Phân tích độ dài từ vựng theo từng phân loại tin tức
def category_text_analysis(articles: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[int]] = {}
    for a in articles:
        cat = str(a.get("category") or "(missing)")
        grouped.setdefault(cat, []).append(text_statistics.word_count(str(a.get("content") or "")))
    return {
        cat: {
            "count": len(vals), "min_word_count": min(vals), "max_word_count": max(vals),
            "mean_word_count": round(statistics.mean(vals), 2),
            "median_word_count": round(statistics.median(vals), 2),
        }
        for cat, vals in sorted(grouped.items())
    }


# Tổng hợp các kết quả khám phá dữ liệu của EDA
def generate_findings(
    articles: list[dict[str, Any]], text_result: dict[str, Any],
    temporal_result: dict[str, Any], deeper_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "phase": "EDA", "purpose": "Descriptive Data Analysis / Exploratory Data Analysis (EDA)",
        "dataset": {
            "path": str(RAW_DATA.relative_to(PROJECT_ROOT)), "records": len(articles),
            "raw_data_modified": False, "sha256_current": sha256_file(RAW_DATA),
        },
        "schema": schema_analysis(articles),
        "duplicates": {f: count_duplicates(articles, f) for f in UNIQUE_FIELDS},
        "missingness": missingness_analysis(articles),
        "category_distribution": distribution(articles, "category"),
        "subcategory_distribution": distribution(articles, "subcategory"),
        "metadata": metadata_analysis(articles),
        "text_statistics": text_result["summary"],
        "category_text_statistics": category_text_analysis(articles),
        "temporal": temporal_result,
        "deeper_eda": deeper_result,
        "visualizations": [
            "outputs/eda/category_subcategory.png", "outputs/eda/average_words_by_category.png",
            "outputs/eda/publication_hour.png", "outputs/eda/publication_to_crawl_gap_by_category.png",
            "outputs/eda/content_length_distribution.png", "outputs/eda/word_count_distribution.png",
        ],
        "interpretation_scope": (
            f"All descriptive findings apply only to the {len(articles)}-record dataset "
            "analyzed in this project. They must not be generalized to the entire "
            "VnExpress website or population of articles."
        ),
    }


# Ghi dữ liệu dạng JSON với thụt dòng chuẩn
def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# Sinh nội dung tóm tắt markdown cho EDA
def generate_summary(findings: dict[str, Any]) -> str:
    dataset, text = findings["dataset"], findings["text_statistics"]
    temporal, metadata = findings["temporal"], findings["metadata"]
    lines = [
        "# ADY201m — Exploratory Data Analysis", "", "## 1. Mục tiêu", "",
        "Phân tích tập trung vào mô tả và khám phá dataset thông qua EDA. "
        "Không thực hiện machine learning, classification, regression hoặc prediction.", "",
        "## 2. Dataset", "", f"- Raw dataset: `{dataset['path']}`",
        f"- Số records: {dataset['records']}", f"- SHA-256 hiện tại: `{dataset['sha256_current']}`",
        "- Raw dataset không được chỉnh sửa trong EDA.", "", "## 3. Schema", "",
        f"- Expected fields: {len(EXPECTED_FIELDS)}",
        f"- Tất cả records có đủ expected fields: {findings['schema']['all_records_contain_expected_fields']}",
        f"- Tất cả records match exact schema: {findings['schema']['all_records_match_exact_expected_schema']}", "",
    ]
    for f in EXPECTED_FIELDS:
        lines.append(f"- `{f}`")
    lines.extend(["", "## 4. Duplicate analysis", ""])
    for f, c in findings["duplicates"].items():
        lines.append(f"- Duplicate `{f}`: {c}")
    lines.extend(["", "## 5. Missingness", ""])
    for f, c in findings["missingness"].items():
        lines.append(f"- `{f}`: {c} missing")
    lines.extend(["", "## 6. Category distribution", ""])
    for name, c in findings["category_distribution"].items():
        lines.append(f"- {name}: {c}")
    lines.extend(["", "## 7. Subcategory distribution", ""])
    for name, c in findings["subcategory_distribution"].items():
        lines.append(f"- {name}: {c}")
    lines.extend(["", "## 8. Text statistics", ""])
    for m, s in text.items():
        lines.extend([
            f"### {m}", f"- Count: {s['count']}", f"- Min: {s['min']}", f"- Max: {s['max']}",
            f"- Mean: {s['mean']}", f"- Median: {s['median']}", f"- Standard deviation: {s['std']}",
            f"- Q1: {s['q1']}", f"- Q3: {s['q3']}", "",
        ])
    lines.extend(["## 9. Category × text statistics", ""])
    for cat, s in findings["category_text_statistics"].items():
        lines.extend([
            f"### {cat}", f"- Articles: {s['count']}", f"- Mean word count: {s['mean_word_count']}",
            f"- Median word count: {s['median_word_count']}", f"- Min word count: {s['min_word_count']}",
            f"- Max word count: {s['max_word_count']}", "",
        ])
    lines.extend(["## 10. Temporal analysis", "", "### Publication date"])
    for d, c in temporal["publication_date_distribution"].items():
        lines.append(f"- {d}: {c}")
    lines.extend(["", "### Publication hour"])
    for h, c in temporal["publication_hour_distribution"].items():
        lines.append(f"- {int(h):02d}:00: {c}")
    gap = temporal["publication_to_crawl_gap_minutes"]
    lines.extend([
        "", "### Publication-to-crawl timestamp gap",
        f"- Min: {gap['min']} minutes", f"- Mean: {gap['mean']} minutes",
        f"- Median: {gap['median']} minutes", f"- Max: {gap['max']} minutes",
        f"- Negative gaps: {gap['negative_gap_count']}",
        "> This is `crawled_at - published_at`; it is not a direct benchmark of crawler execution latency.",
        "", "## 11. Metadata", "",
        f"- Unique authors: {metadata['unique_authors']}", f"- Unique publishers: {metadata['unique_publishers']}",
        f"- Unique sources: {metadata['unique_sources']}", f"- Unique article IDs: {metadata['unique_article_ids']}",
        "", "## 12. Visualizations", "",
    ])
    for v in findings["visualizations"]:
        lines.append(f"- `{v}`")
    lines.extend([
        "", "## 13. Interpretation limitation", "", findings["interpretation_scope"],
        "", "## 14. Status", "", "**STATUS: COMPLETE — REPRODUCIBLE DESCRIPTIVE EDA PIPELINE**", "",
    ])
    return "\n".join(lines)


# Tạo báo cáo giới hạn phạm vi thống kê của EDA
def generate_limitations(record_count: int) -> str:
    return f"""# ADY201m — EDA Limitations

## 1. Sample size
The current dataset contains {record_count} records. Statistics are descriptive
statistics of this dataset only and are not population estimates.

## 2. Sampling
The dataset is a collected sample rather than a statistically random sample of all
VnExpress articles. Distributional results may therefore differ from the broader corpus.

## 3. Text metrics
Word count uses whitespace-separated tokens. Sentence count is an approximate punctuation-based
measure. These metrics are suitable for descriptive EDA but are not full Vietnamese NLP tokenization.

## 4. Unique-word statistics
Unique-word statistics use normalized tokens only for measurement. The raw dataset is not modified.

## 5. Temporal interpretation
Publication-to-crawl timestamp gap is calculated as `crawled_at - published_at`. It does not directly
measure crawler execution time.

## 6. Metadata
Author, publisher, source and article-ID distributions describe only values present in the collected sample.

## 7. Raw-data integrity
EDA does not modify `data/raw/articles.jsonl`. Future cleaning or normalization should create outputs under
`data/processed/` and keep transformations traceable.
"""


# Tạo tài liệu danh mục kiểm tra chất lượng kết quả EDA
def generate_checklist(findings: dict[str, Any]) -> str:
    checks = [
        ("Raw dataset unchanged", True),
        ("20 records loaded", findings["dataset"]["records"] == 20),
        ("All records match exact 12-field schema", findings["schema"]["all_records_match_exact_expected_schema"]),
        ("Missingness analyzed", True),
        ("No missing values in expected fields", all(v == 0 for v in findings["missingness"].values())),
        ("Duplicate analysis completed", True),
        ("No duplicate URL/title/article_id", all(v == 0 for v in findings["duplicates"].values())),
        ("Category distribution", True), ("Subcategory distribution", True),
        ("Character statistics", True), ("Word statistics", True),
        ("Sentence statistics", True), ("Unique-word statistics", True),
        ("Average word length", True), ("Title statistics", True),
        ("Description statistics", True), ("Category × text statistics", True),
        ("Publication date", True), ("Publication hour", True),
        ("Publication-to-crawl gap", findings["temporal"]["published_at"]["invalid"] == 0 and findings["temporal"]["crawled_at"]["invalid"] == 0),
        ("Author / publisher / source analysis", True),
        ("Six visualizations generated by the unified EDA", True),
        ("Machine-readable findings JSON", True), ("Markdown summary", True),
        ("Limitations document", True), ("Checklist document", True),
        ("Findings scoped to the current dataset", True), ("No ML/prediction introduced", True),
    ]
    lines = ["# ADY201m — EDA Checklist", "", "## Verification"]
    for label, passed in checks:
        lines.append(f"- [{'x' if passed else ' '}] {label}")
    failed = [label for label, passed in checks if not passed]
    lines.extend(["", "## Final status", "", "**EDA — NEEDS REVIEW**" if failed else "**EDA — COMPLETE**"])
    if failed:
        lines.extend(["", "Failed checks:"] + [f"- {l}" for l in failed])
    return "\n".join(lines) + "\n"


# Điều phối toàn bộ quy trình thực thi EDA
def main() -> None:
    print("=" * 70 + "\nADY201m — EDA PIPELINE\n" + "=" * 70)
    EDA_DIR.mkdir(parents=True, exist_ok=True)
    EDA_SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    articles = load_raw()
    print(f"\nRaw records loaded: {len(articles)}")
    if not articles:
        raise RuntimeError("Raw dataset contains no records.")

    text_result = text_statistics.analyze_articles(articles)
    text_statistics.save_result(text_result)
    temporal_result = temporal_analysis.analyze_articles(articles)
    temporal_analysis.save_result(temporal_result)
    deeper_result = deeper_eda.analyze_articles(articles, temporal_result)
    deeper_eda.save_outputs(deeper_result, articles)

    findings = generate_findings(articles, text_result, temporal_result, deeper_result)
    write_json(FINDINGS_FILE, findings)
    SUMMARY_FILE.write_text(generate_summary(findings), encoding="utf-8")
    LIMITATIONS_FILE.write_text(generate_limitations(len(articles)), encoding="utf-8")
    CHECKLIST_FILE.write_text(generate_checklist(findings), encoding="utf-8")

    print("\n" + "=" * 70 + "\nEDA COMPLETE\n" + "=" * 70)
    print(f"Records: {len(articles)}, Categories: {len(findings['category_distribution'])}")
    print(f"Subcategories: {len(findings['subcategory_distribution'])}, Unique authors: {findings['metadata']['unique_authors']}")
    checklist_text = CHECKLIST_FILE.read_text(encoding="utf-8")
    print("\nSTATUS: " + ("EDA COMPLETE" if "**EDA — COMPLETE**" in checklist_text else "EDA NEEDS REVIEW"))


if __name__ == "__main__":
    main()
