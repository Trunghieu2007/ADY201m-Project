"""
Bộ kiểm thử hồi quy và tính toàn vẹn hệ thống ADY201m.
Bảo đảm tính chính xác và an toàn của toàn bộ quy trình: Crawler (E) -> Preprocess (T) -> Database (L).
"""
from __future__ import annotations

import json
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
from src.crawler.validate_raw import count_empty_fields
from src.database.sqlserver import (
    FEATURE_COLUMNS,
    build_connection_string,
    feature_values,
    load_processed_records,
    split_sql_batches,
    verify_database,
)
from src.eda.text_statistics import sentence_count, word_count
from src.organization.category_organizer import (
    CANONICAL_CATEGORIES,
    compute_category_summary,
    extract_category_from_url,
    get_top_keywords,
    organize_articles,
)
from src.preprocessing.preprocess import preprocess_record
from src.validation.create_manifest import EXPECTED_SCHEMA, inspect_schema


class ProjectTests(unittest.TestCase):
    """Kiểm thử tính nhất quán cấu hình, bóc tách bài viết và tính toàn vẹn dữ liệu thô."""

    def test_config_sources_are_consistent(self):
        """Kiểm tra tính khớp nối giữa danh mục CATEGORIES và nguồn RSS_FEEDS / SITEMAP_URLS."""
        self.assertEqual(set(CATEGORIES.values()), {label for label, _url in RSS_FEEDS.values()})
        self.assertEqual(set(CATEGORIES.keys()), set(RSS_FEEDS.keys()))
        self.assertGreaterEqual(len(SITEMAP_URLS), 2)
        for url in SITEMAP_URLS:
            self.assertTrue(url.startswith("https://vnexpress.net/"))
            self.assertTrue(url.endswith(".xml"))

    def test_sitemap_module_imports(self):
        """Kiểm tra SitemapCrawler có thể import và chứa phương thức discover."""
        self.assertTrue(hasattr(SitemapCrawler, "discover"))
        self.assertTrue(callable(getattr(SitemapCrawler, "discover")))

    def test_article_parser_excludes_title_description_and_duplicate_blocks(self):
        """Kiểm tra parser bóc tách chính xác nội dung, loại bỏ khối trùng lặp và làm sạch tác giả."""
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
        # Kiểm tra thêm cơ chế lọc tác giả rác và prefix
        self.assertIsNone(ArticleCrawler.clean_author("VnExpress"))
        self.assertIsNone(ArticleCrawler.clean_author("Báo VnExpress"))
        self.assertEqual(ArticleCrawler.clean_author("Tác giả: Nguyễn Văn A"), "Nguyễn Văn A")

    def test_basic_text_metrics_are_defined(self):
        """Kiểm tra các hàm tính toán chỉ số văn bản cơ bản (đếm từ, đếm câu)."""
        self.assertEqual(word_count("một hai ba"), 3)
        self.assertEqual(word_count(""), 0)
        self.assertEqual(sentence_count("Một câu. Câu hai!"), 2)
        self.assertEqual(sentence_count(""), 0)

    def test_manifest_schema_checks_each_record(self):
        """Kiểm tra hàm inspect_schema phát hiện chính xác trường thiếu hoặc trường thừa."""
        good = {field: None for field in EXPECTED_SCHEMA}
        bad = dict(good)
        bad.pop("title")
        bad["unexpected"] = "value"
        result = inspect_schema([good, bad])
        self.assertFalse(result["schema_matches_expected"])
        self.assertEqual(result["records_with_missing_fields"]["record_2"], ["title"])
        self.assertEqual(result["records_with_unexpected_fields"]["record_2"], ["unexpected"])

    def test_nullable_metadata_is_not_a_nonempty_field_failure(self):
        """Kiểm tra các trường nullable (author, subcategory, article_id) không bị coi là lỗi rỗng."""
        record = {field: "x" for field in EXPECTED_SCHEMA}
        record["author"] = None
        record["subcategory"] = None
        record["article_id"] = None
        missing = count_empty_fields([record])
        self.assertNotIn("author", missing)
        self.assertNotIn("subcategory", missing)
        self.assertNotIn("article_id", missing)


class Phase3Tests(unittest.TestCase):
    """Kiểm thử quy trình tiền xử lý dữ liệu và tính bất biến của dữ liệu gốc."""

    def test_phase3_modules_import(self):
        """Kiểm tra hàm preprocess_record có thể import và thực thi."""
        self.assertTrue(callable(preprocess_record))

    def test_phase3_is_non_destructive(self):
        """Kiểm tra quá trình tiền xử lý bảo toàn 100% dữ liệu gốc (Non-destructive)."""
        record = {
            "url": "https://example.com/a", "title": "  Tiêu đề  ", "description": "Mô tả",
            "content": "Một câu. Câu hai!", "author": "Bảo Bảo ( Tổng hợp )",
            "publisher": "VnExpress", "published_at": "2026-09-25T10:00:00+07:00",
            "category": "Sức khỏe", "subcategory": "Các bệnh", "article_id": "1",
            "crawled_at": "2026-09-25T10:10:00+07:00", "source": "vnexpress"
        }
        original = dict(record)
        out = preprocess_record(record, {"Sức khỏe": 1}, {"Các bệnh": 1})
        # Dữ liệu gốc truyền vào không bị sửa đổi
        self.assertEqual(record, original)
        # Trường tác giả gốc được giữ nguyên vẹn
        self.assertEqual(out["author"], "Bảo Bảo ( Tổng hợp )")
        # Trường phái sinh author_clean được chuẩn hóa
        self.assertEqual(out["processed_metadata"]["author_clean"], "Bảo Bảo tổng hợp")
        # Chỉ số câu được tính toán chính xác
        self.assertEqual(out["features"]["sentence_count"], 2)
        # Đảm bảo có đủ các trường đặc trưng mô tả chính
        for feat in ("char_count", "word_count", "lexical_diversity", "publication_hour", "publication_weekday"):
            self.assertIn(feat, out["features"])

    def test_phase3_preserves_raw_core_fields(self):
        """Kiểm tra toàn bộ các trường cốt lõi của raw data được giữ nguyên vẹn ở tầng ngoài."""
        record = {
            "url": "u", "title": "t", "description": "d", "content": "c",
            "author": None, "publisher": "p", "published_at": "2026-01-01T00:00:00+00:00",
            "category": "A", "subcategory": None, "article_id": "1",
            "crawled_at": "x", "source": "s"
        }
        out = preprocess_record(record, {"A": 1}, {})
        for k, v in record.items():
            self.assertEqual(out[k], v, f"Trường {k} bị thay đổi sau khi preprocess")


class CategoryOrganizationTests(unittest.TestCase):
    """Kiểm thử tự động tổ chức chuyên mục và trích xuất từ khóa xu hướng."""

    def test_canonical_categories_contain_five_targets(self):
        """Kiểm tra danh sách 5 chuyên mục mục tiêu chuẩn hóa."""
        targets = {"Thời sự", "Kinh doanh", "Bất động sản", "Khoa học công nghệ", "Sức khỏe"}
        self.assertEqual(set(CANONICAL_CATEGORIES.values()), targets)

    def test_extract_category_from_url(self):
        """Kiểm tra hàm ánh xạ URL bài viết sang tên chuyên mục tiếng Việt chuẩn."""
        self.assertEqual(extract_category_from_url("https://vnexpress.net/thoi-su/bai-viet-1.html"), "Thời sự")
        self.assertEqual(extract_category_from_url("https://vnexpress.net/kinh-doanh/doanh-nghiep-2.html"), "Kinh doanh")
        self.assertEqual(extract_category_from_url("https://vnexpress.net/bat-dong-san/tin-3.html"), "Bất động sản")
        self.assertEqual(extract_category_from_url("https://vnexpress.net/suc-khoe/benh-4.html"), "Sức khỏe")
        self.assertEqual(extract_category_from_url("https://vnexpress.net/khoa-hoc-cong-nghe/tin-5.html"), "Khoa học công nghệ")

    def test_organize_articles_groups_by_category(self):
        """Kiểm tra hàm nhóm các bài viết theo chuyên mục tương ứng."""
        records = [
            {"category": "Thời sự", "title": "Tin tức 1"},
            {"category": "Thời sự", "title": "Tin tức 2"},
            {"category": "Kinh doanh", "title": "Kinh tế 1"},
        ]
        grouped = organize_articles(records)
        self.assertEqual(len(grouped["Thời sự"]), 2)
        self.assertEqual(len(grouped["Kinh doanh"]), 1)

    def test_get_top_keywords_removes_stopwords(self):
        """Kiểm tra bộ lọc từ khóa nóng loại bỏ chính xác các từ dừng (stopwords tiếng Việt)."""
        records = [{"content": "thị trường bất động sản và các dự án căn hộ trong và ngoài nước"}]
        kw = dict(get_top_keywords(records, top_n=5))
        self.assertIn("bất", kw)
        self.assertNotIn("và", kw)
        self.assertNotIn("trong", kw)

    def test_compute_category_summary_metrics(self):
        """Kiểm tra tính toán số liệu thống kê tổng hợp chuyên mục và tỷ lệ phần trăm."""
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
        """Kiểm tra tệp category_summary.json trên đĩa tồn tại và chứa cấu trúc hợp lệ."""
        path = Path("data/processed/category_summary.json")
        self.assertTrue(path.exists(), f"Không tìm thấy tệp {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(data["total_articles"], 20)
        self.assertEqual(data["total_categories"], 5)
        for cat in CANONICAL_CATEGORIES.values():
            self.assertIn(cat, data["categories"])


class Phase6Tests(unittest.TestCase):
    """Kiểm thử tính sẵn sàng của tầng CSDL SQL Server 3NF và Streamlit Dashboard."""

    def test_phase6_sql_modules_import(self):
        """Kiểm tra các hàm tương tác SQL Server import thành công và đọc được script SQL."""
        self.assertTrue(callable(build_connection_string))
        self.assertTrue(callable(feature_values))
        batches = split_sql_batches(Path("sql/create_tables.sql").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(batches), 6)

    def test_phase6_schema_contains_core_tables_and_keys(self):
        """Kiểm tra schema CSDL chứa đủ 5 bảng chuẩn 3NF và các ràng buộc khóa chính/khóa ngoại."""
        sql = Path("sql/create_tables.sql").read_text(encoding="utf-8")
        for token in [
            "dbo.Categories", "dbo.Subcategories", "dbo.Authors",
            "dbo.Articles", "dbo.ArticleFeatures", "PK_Articles",
            "FK_Articles_Categories", "FK_ArticleFeatures_Articles",
        ]:
            self.assertIn(token, sql, f"Thiếu định nghĩa {token} trong create_tables.sql")

    def test_phase6_feature_whitelist_excludes_target_derived_columns(self):
        """Kiểm tra FEATURE_COLUMNS chỉ gồm đúng 13 biến mô tả, không chứa cột mã hóa ML/danh mục."""
        records = load_processed_records()
        self.assertEqual(len(FEATURE_COLUMNS), 13)
        self.assertNotIn("category_id", FEATURE_COLUMNS)
        self.assertNotIn("subcategory_id", FEATURE_COLUMNS)
        self.assertEqual(len(feature_values(records[0])), len(FEATURE_COLUMNS))

    def test_phase6_streamlit_dashboard_exists(self):
        """Kiểm tra mã nguồn Streamlit Dashboard và tệp requirements-streamlit.txt tồn tại."""
        self.assertTrue(Path("dashboard/app.py").exists())
        self.assertTrue(Path("requirements-streamlit.txt").exists())

    def test_phase6_update_sql_is_parameterized(self):
        """Kiểm tra câu lệnh SQL Upsert sử dụng tham số hóa parameterized (chống SQL Injection)."""
        sql = Path("sql/upsert_article.sql").read_text(encoding="utf-8")
        self.assertIn("WHERE article_id = ?", sql)
        self.assertNotIn("UPDATE dbo.Articles SET url = '", sql)

    def test_phase6_database_verification_and_queries(self):
        """Kiểm tra hàm verify_database có thể import và tệp queries.sql chứa đủ truy vấn Window Functions."""
        self.assertTrue(callable(verify_database))
        sql = Path("sql/queries.sql").read_text(encoding="utf-8")
        self.assertIn("ROW_NUMBER() OVER", sql)

    def test_phase6_processed_input_is_20_records(self):
        """Kiểm tra dữ liệu nạp CSDL articles_processed.jsonl có đủ số bản ghi hợp lệ (>= 20 bản ghi)."""
        records = load_processed_records()
        self.assertGreaterEqual(len(records), 20)
        for r in records:
            self.assertTrue(bool(r.get("article_id")))
            self.assertTrue(bool(r.get("url")))
            self.assertTrue(bool(r.get("title")))
            self.assertIn("features", r)

    def test_phase6_erd_diagram_and_draw_module(self):
        """Kiểm tra module vẽ ERD và tệp ảnh sơ đồ quan hệ thực thể tồn tại hợp lệ."""
        from src.database.draw_erd import draw_erd
        self.assertTrue(callable(draw_erd))
        erd_path = Path("outputs/database/erd_diagram.png")
        self.assertTrue(erd_path.exists(), "Tệp sơ đồ ERD outputs/database/erd_diagram.png không tồn tại")
        self.assertGreater(erd_path.stat().st_size, 10000, "Tệp sơ đồ ERD quá nhỏ hoặc rỗng")


if __name__ == "__main__":
    unittest.main()
