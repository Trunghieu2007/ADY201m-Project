import json
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from src.crawler.crawler import (
    CATEGORIES,
    RSS_FEEDS,
    SITEMAP_URLS,
    ArticleCrawler,
    SitemapCrawler,
)
from src.eda.text_statistics import sentence_count, word_count
from src.organization.category_organizer import (
    CANONICAL_CATEGORIES,
    compute_category_summary,
    extract_category_from_url,
    get_top_keywords,
    organize_articles,
)
from src.validation.create_manifest import EXPECTED_SCHEMA, inspect_schema
from src.validation.validate_raw import count_empty_fields


class ProjectTests(unittest.TestCase):
    def test_config_sources_are_consistent(self):
        self.assertEqual(set(CATEGORIES.values()), {label for label, _url in RSS_FEEDS.values()})
        self.assertGreaterEqual(len(SITEMAP_URLS), 2)

    def test_sitemap_module_imports(self):
        self.assertTrue(hasattr(SitemapCrawler, "discover"))

    def test_article_parser_excludes_title_description_and_duplicate_blocks(self):
        html = """
        <html><body>
          <h1 class="title-detail">Test title</h1>
          <p class="description">Test description</p>
          <div class="fck_detail">
            <p>Test title</p>
            <p>Test description</p>
            <p>First paragraph</p>
            <p>First paragraph</p>
            <p align="right"><strong>Author Name</strong> Nhóm thiết kế: Team X Ảnh: Photo Y</p>
            <span id="article-end"></span>
            <p>Related content</p>
          </div>
        </body></html>
        """
        crawler = ArticleCrawler()
        soup = BeautifulSoup(html, "lxml")
        content = crawler.extract_article_content(soup)
        author = crawler.extract_author(soup)
        self.assertEqual(content, "First paragraph")
        self.assertEqual(author, "Author Name")

    def test_basic_text_metrics_are_defined(self):
        self.assertEqual(word_count("một hai ba"), 3)
        self.assertEqual(sentence_count("Một câu. Câu hai!"), 2)

    def test_manifest_schema_checks_each_record(self):
        good = {field: None for field in EXPECTED_SCHEMA}
        bad = dict(good)
        bad.pop("title")
        bad["unexpected"] = "value"
        result = inspect_schema([good, bad])
        self.assertFalse(result["schema_matches_expected"])
        self.assertEqual(result["records_with_missing_fields"]["record_2"], ["title"])
        self.assertEqual(result["records_with_unexpected_fields"]["record_2"], ["unexpected"])

    def test_nullable_metadata_is_not_a_nonempty_field_failure(self):
        record = {field: "x" for field in EXPECTED_SCHEMA}
        record["author"] = None
        record["subcategory"] = None
        record["article_id"] = None
        missing = count_empty_fields([record])
        self.assertNotIn("author", missing)
        self.assertNotIn("subcategory", missing)
        self.assertNotIn("article_id", missing)


class Phase3Tests(unittest.TestCase):
    def test_phase3_modules_import(self):
        from src.preprocessing.preprocess import preprocess_record
        self.assertTrue(callable(preprocess_record))

    def test_phase3_is_non_destructive(self):
        from src.preprocessing.preprocess import preprocess_record
        record = {
            "url": "https://example.com/a", "title": "  Tiêu đề  ", "description": "Mô tả",
            "content": "Một câu. Câu hai!", "author": "Bảo Bảo ( Tổng hợp )",
            "publisher": "VnExpress", "published_at": "2026-09-25T10:00:00+07:00",
            "category": "Sức khỏe", "subcategory": "Các bệnh", "article_id": "1",
            "crawled_at": "2026-09-25T10:10:00+07:00", "source": "vnexpress"
        }
        original = dict(record)
        out = preprocess_record(record, {"Sức khỏe": 1}, {"Các bệnh": 1})
        self.assertEqual(record, original)
        self.assertEqual(out["author"], "Bảo Bảo ( Tổng hợp )")
        self.assertEqual(out["processed_metadata"]["author_clean"], "Bảo Bảo tổng hợp")
        self.assertEqual(out["features"]["sentence_count"], 2)

    def test_phase3_preserves_raw_core_fields(self):
        from src.preprocessing.preprocess import preprocess_record
        record = {"url":"u","title":"t","description":"d","content":"c","author":None,"publisher":"p","published_at":"2026-01-01T00:00:00+00:00","category":"A","subcategory":None,"article_id":"1","crawled_at":"x","source":"s"}
        out = preprocess_record(record, {"A":1}, {})
        for k, v in record.items():
            self.assertEqual(out[k], v)


class CategoryOrganizationTests(unittest.TestCase):
    def test_canonical_categories_contain_five_targets(self):
        targets = {"Thời sự", "Kinh doanh", "Bất động sản", "Khoa học công nghệ", "Sức khỏe"}
        self.assertEqual(set(CANONICAL_CATEGORIES.values()), targets)

    def test_extract_category_from_url(self):
        self.assertEqual(extract_category_from_url("https://vnexpress.net/thoi-su/bai-viet-1.html"), "Thời sự")
        self.assertEqual(extract_category_from_url("https://vnexpress.net/kinh-doanh/doanh-nghiep-2.html"), "Kinh doanh")
        self.assertEqual(extract_category_from_url("https://vnexpress.net/bat-dong-san/tin-3.html"), "Bất động sản")
        self.assertEqual(extract_category_from_url("https://vnexpress.net/suc-khoe/benh-4.html"), "Sức khỏe")

    def test_organize_articles_groups_by_category(self):
        records = [
            {"category": "Thời sự", "title": "Tin tức 1"},
            {"category": "Thời sự", "title": "Tin tức 2"},
            {"category": "Kinh doanh", "title": "Kinh tế 1"},
        ]
        grouped = organize_articles(records)
        self.assertEqual(len(grouped["Thời sự"]), 2)
        self.assertEqual(len(grouped["Kinh doanh"]), 1)

    def test_get_top_keywords_removes_stopwords(self):
        records = [{"content": "thị trường bất động sản và các dự án căn hộ trong và ngoài nước"}]
        kw = dict(get_top_keywords(records, top_n=5))
        self.assertIn("bất", kw)
        self.assertNotIn("và", kw)
        self.assertNotIn("trong", kw)

    def test_compute_category_summary_metrics(self):
        records = [
            {"category": "Thời sự", "subcategory": "Đô thị", "author": "Nguyễn Văn A", "content": "Tin tức đô thị hôm nay phát triển"},
            {"category": "Kinh doanh", "subcategory": "Thị trường", "author": "Trần B", "content": "Thị trường chứng khoán tăng điểm tốt"},
        ]
        summary = compute_category_summary(records)
        self.assertEqual(summary["total_articles"], 2)
        self.assertEqual(summary["total_categories"], 2)
        self.assertEqual(summary["categories"]["Thời sự"]["count"], 1)
        self.assertEqual(summary["categories"]["Thời sự"]["percentage"], 50.0)

    def test_category_summary_file_exists_and_valid(self):
        path = Path("data/processed/category_summary.json")
        self.assertTrue(path.exists())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["total_articles"], 20)
        self.assertEqual(data["total_categories"], 5)


class Phase6Tests(unittest.TestCase):
    def test_phase6_sql_modules_import(self):
        from src.database.sqlserver import build_connection_string, feature_values, split_sql_batches
        self.assertTrue(callable(build_connection_string))
        self.assertTrue(callable(feature_values))
        self.assertGreaterEqual(len(split_sql_batches(Path("sql/create_tables.sql").read_text(encoding="utf-8"))), 6)

    def test_phase6_schema_contains_core_tables_and_keys(self):
        sql = Path("sql/create_tables.sql").read_text(encoding="utf-8")
        for token in [
            "dbo.Categories", "dbo.Subcategories", "dbo.Authors",
            "dbo.Articles", "dbo.ArticleFeatures", "PK_Articles",
            "FK_Articles_Categories", "FK_ArticleFeatures_Articles",
        ]:
            self.assertIn(token, sql)

    def test_phase6_feature_whitelist_excludes_target_derived_columns(self):
        from src.database.sqlserver import FEATURE_COLUMNS, load_processed_records, feature_values
        records = load_processed_records()
        self.assertEqual(len(FEATURE_COLUMNS), 13)
        self.assertNotIn("category_id", FEATURE_COLUMNS)
        self.assertNotIn("subcategory_id", FEATURE_COLUMNS)
        self.assertEqual(len(feature_values(records[0])), len(FEATURE_COLUMNS))

    def test_phase6_streamlit_dashboard_exists(self):
        self.assertTrue(Path("dashboard/app.py").exists())
        self.assertTrue(Path("requirements-streamlit.txt").exists())

    def test_phase6_update_sql_is_parameterized(self):
        sql = Path("sql/upsert_article.sql").read_text(encoding="utf-8")
        self.assertIn("WHERE article_id = ?", sql)
        self.assertNotIn("UPDATE dbo.Articles SET url = '" , sql)

    def test_phase6_processed_input_is_20_records(self):
        from src.database.sqlserver import load_processed_records
        self.assertEqual(len(load_processed_records()), 20)


if __name__ == "__main__":
    unittest.main()
