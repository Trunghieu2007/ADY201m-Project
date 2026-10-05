from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Iterable

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_SQL = ROOT / "sql" / "create_tables.sql"
QUERIES_SQL = ROOT / "sql" / "queries.sql"
UPSERT_SQL = ROOT / "sql" / "upsert_article.sql"
PROCESSED_JSONL = ROOT / "data" / "processed" / "articles_processed.jsonl"
DATABASE_MANIFEST = ROOT / "outputs" / "database" / "database_manifest.json"
DATABASE_SUMMARY = ROOT / "outputs" / "database" / "database_summary.md"

FEATURE_COLUMNS = (
    "char_count", "word_count", "sentence_count", "unique_word_count",
    "lexical_diversity", "avg_word_length", "title_char_count", "title_word_count",
    "description_char_count", "description_word_count", "title_to_content_word_ratio",
    "publication_hour", "publication_weekday",
)


def resolve_default_driver() -> str:
    """Tự động nhận diện ODBC Driver cho SQL Server khả dụng trên hệ thống."""
    explicit = os.getenv("ADY_SQLSERVER_DRIVER")
    if explicit:
        return explicit
    try:
        import pyodbc
        available = pyodbc.drivers()
        for preferred in [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server",
        ]:
            if preferred in available:
                return preferred
    except Exception:
        pass
    return "ODBC Driver 17 for SQL Server"


def resolve_default_server(driver: str) -> str:
    """Tự động kiểm tra instance SQL Server cục bộ (SQLEXPRESS hoặc default localhost)."""
    explicit = os.getenv("ADY_SQLSERVER_SERVER")
    if explicit:
        return explicit
    try:
        import pyodbc
        for candidate in ["localhost\\SQLEXPRESS", "localhost", "."]:
            try:
                conn = pyodbc.connect(
                    f"DRIVER={{{driver}}};SERVER={candidate};Trusted_Connection=yes;TrustServerCertificate=yes;",
                    autocommit=True,
                    timeout=2,
                )
                conn.close()
                return candidate
            except Exception:
                continue
    except Exception:
        pass
    return "localhost"


# Xây dựng chuỗi kết nối Microsoft SQL Server từ biến môi trường hoặc tự động nhận diện
def build_connection_string() -> str:
    explicit = os.getenv("ADY_SQLSERVER_CONNECTION_STRING")
    if explicit:
        return explicit
    driver = resolve_default_driver()
    server = resolve_default_server(driver)
    database = os.getenv("ADY_SQLSERVER_DATABASE", "ADY201m")
    trusted = os.getenv("ADY_SQLSERVER_TRUSTED_CONNECTION", "yes").strip().lower()
    trust_cert = os.getenv("ADY_SQLSERVER_TRUST_SERVER_CERTIFICATE", "yes")

    parts = [f"DRIVER={{{driver}}}", f"SERVER={server}", f"DATABASE={database}", f"TrustServerCertificate={trust_cert}"]
    if trusted in {"yes", "true", "1"}:
        parts.append("Trusted_Connection=yes")
    else:
        username, password = os.getenv("ADY_SQLSERVER_USERNAME"), os.getenv("ADY_SQLSERVER_PASSWORD")
        if not username or password is None:
            raise RuntimeError("SQL authentication selected but credentials missing.")
        parts.extend([f"UID={username}", f"PWD={password}"])
    return ";".join(parts) + ";"


# Tạo kết nối pyodbc tới SQL Server theo cấu hình môi trường
def get_connection():
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("pyodbc is required for SQL Server integration: pip install -r requirements.txt") from exc
    conn = pyodbc.connect(build_connection_string(), autocommit=False)
    try:
        import struct

        def handle_datetimeoffset(dto_value: bytes) -> str:
            tup = struct.unpack("=6hI2h", dto_value)
            tz_sign = "+" if tup[7] >= 0 else "-"
            return f"{tup[0]:04d}-{tup[1]:02d}-{tup[2]:02d}T{tup[3]:02d}:{tup[4]:02d}:{tup[5]:02d}{tz_sign}{abs(tup[7]):02d}:{abs(tup[8]):02d}"

        conn.add_output_converter(-155, handle_datetimeoffset)
    except Exception:
        pass
    return conn


# Đọc các bản ghi đã tiền xử lý từ file JSONL
def load_processed_records(path: Path = PROCESSED_JSONL) -> list[dict[str, Any]]:
    import json
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at line {line_no}: {exc}") from exc
            if not record.get("article_id") or not record.get("category"):
                raise ValueError(f"Missing core fields at line {line_no}")
            records.append(record)
    return records


# Trích xuất 13 giá trị đặc trưng hợp lệ không phụ thuộc biến mục tiêu
def feature_values(record: dict[str, Any]) -> tuple[Any, ...]:
    features = record.get("features") or {}
    return tuple(features.get(col) for col in FEATURE_COLUMNS)


# Tách câu lệnh SQL nhiều phần theo từ khóa GO
def split_sql_batches(sql_text: str) -> list[str]:
    batches, current = [], []
    for line in sql_text.splitlines():
        if line.strip().upper() == "GO":
            batch = "\n".join(current).strip()
            if batch:
                batches.append(batch)
            current = []
        else:
            current.append(line)
    batch = "\n".join(current).strip()
    if batch:
        batches.append(batch)
    return batches


# Thực thi kịch bản tạo bảng và ràng buộc khóa cho CSDL SQL Server
def execute_schema(cursor: Any, schema_path: Path = SCHEMA_SQL) -> int:
    batches = split_sql_batches(schema_path.read_text(encoding="utf-8"))
    for batch in batches:
        cursor.execute(batch)
    return len(batches)


# Lấy ID hoặc tạo mới bản ghi cho bảng chiều (Categories, Authors, Subcategories)
def ensure_dimension(cursor: Any, table: str, name: str, *, category_id: Any = None) -> Any:
    if table == "Categories":
        cursor.execute("SELECT category_id FROM dbo.Categories WHERE name = ?", name)
    elif table == "Authors":
        cursor.execute("SELECT author_id FROM dbo.Authors WHERE name = ?", name)
    elif table == "Subcategories":
        cursor.execute("SELECT subcategory_id FROM dbo.Subcategories WHERE category_id = ? AND name = ?", category_id, name)
    else:
        raise ValueError(f"Unsupported dimension table: {table}")
    row = cursor.fetchone()
    if row:
        return row[0]

    if table == "Categories":
        cursor.execute("INSERT INTO dbo.Categories(name) OUTPUT INSERTED.category_id VALUES (?)", name)
    elif table == "Authors":
        cursor.execute("INSERT INTO dbo.Authors(name) OUTPUT INSERTED.author_id VALUES (?)", name)
    else:
        cursor.execute("INSERT INTO dbo.Subcategories(category_id, name) OUTPUT INSERTED.subcategory_id VALUES (?, ?)", category_id, name)
    inserted = cursor.fetchone()
    if not inserted:
        raise RuntimeError(f"Could not create {table} row for {name!r}")
    return inserted[0]


# Chuẩn bị bộ tham số để chèn vào bảng Articles
def article_parameters(record: dict[str, Any], category_id: Any, subcategory_id: Any, author_id: Any) -> tuple[Any, ...]:
    return (
        record.get("article_id"), record.get("url"), record.get("title"), record.get("description"),
        record.get("content"), author_id, record.get("publisher"), record.get("published_at"),
        category_id, subcategory_id, record.get("crawled_at"), record.get("source"),
    )


# Thêm mới một bài viết và các đặc trưng thống kê vào cơ sở dữ liệu
def import_record(cursor: Any, record: dict[str, Any]) -> bool:
    cursor.execute("SELECT 1 FROM dbo.Articles WHERE article_id = ?", record["article_id"])
    if cursor.fetchone():
        return False
    category_id = ensure_dimension(cursor, "Categories", record["category"])
    subcategory_id = ensure_dimension(cursor, "Subcategories", record["subcategory"], category_id=category_id) if record.get("subcategory") else None
    author_name = record.get("processed_metadata", {}).get("author_clean") or record.get("author")
    author_id = ensure_dimension(cursor, "Authors", author_name) if author_name else None

    cursor.execute(
        """INSERT INTO dbo.Articles(
            article_id, url, title, description, content, author_id, publisher,
            published_at, category_id, subcategory_id, crawled_at, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        article_parameters(record, category_id, subcategory_id, author_id),
    )
    cursor.execute(
        """INSERT INTO dbo.ArticleFeatures(
            article_id, char_count, word_count, sentence_count, unique_word_count,
            lexical_diversity, avg_word_length, title_char_count, title_word_count,
            description_char_count, description_word_count, title_to_content_word_ratio,
            publication_hour, publication_weekday
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (record["article_id"],) + feature_values(record),
    )
    return True


# Cập nhật thông tin bài viết và đặc trưng nếu bài viết đã tồn tại
def update_record(cursor: Any, record: dict[str, Any]) -> bool:
    cursor.execute("SELECT 1 FROM dbo.Articles WHERE article_id = ?", record["article_id"])
    if not cursor.fetchone():
        return False
    category_id = ensure_dimension(cursor, "Categories", record["category"])
    subcategory_id = ensure_dimension(cursor, "Subcategories", record["subcategory"], category_id=category_id) if record.get("subcategory") else None
    author_name = record.get("processed_metadata", {}).get("author_clean") or record.get("author")
    author_id = ensure_dimension(cursor, "Authors", author_name) if author_name else None

    cursor.execute(
        """UPDATE dbo.Articles SET
            url = ?, title = ?, description = ?, content = ?, author_id = ?,
            publisher = ?, published_at = ?, category_id = ?, subcategory_id = ?,
            crawled_at = ?, source = ?, updated_at = SYSUTCDATETIME()
        WHERE article_id = ?""",
        (
            record.get("url"), record.get("title"), record.get("description"), record.get("content"),
            author_id, record.get("publisher"), record.get("published_at"), category_id,
            subcategory_id, record.get("crawled_at"), record.get("source"), record["article_id"],
        ),
    )
    feature_sql = """UPDATE dbo.ArticleFeatures SET
        char_count=?, word_count=?, sentence_count=?, unique_word_count=?, lexical_diversity=?,
        avg_word_length=?, title_char_count=?, title_word_count=?, description_char_count=?,
        description_word_count=?, title_to_content_word_ratio=?, publication_hour=?, publication_weekday=?,
        updated_at=SYSUTCDATETIME()
        WHERE article_id=?"""
    cursor.execute(feature_sql, feature_values(record) + (record["article_id"],))
    if cursor.rowcount == 0:
        cursor.execute(
            """INSERT INTO dbo.ArticleFeatures(
                article_id, char_count, word_count, sentence_count, unique_word_count,
                lexical_diversity, avg_word_length, title_char_count, title_word_count,
                description_char_count, description_word_count, title_to_content_word_ratio,
                publication_hour, publication_weekday
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record["article_id"],) + feature_values(record),
        )
    return True


# Đồng bộ danh sách bài viết vào CSDL trong một transaction an toàn
def sync_records(connection: Any, records: Iterable[dict[str, Any]]) -> tuple[int, int]:
    cursor = connection.cursor()
    inserted = updated = 0
    try:
        for record in records:
            if update_record(cursor, record):
                updated += 1
            elif import_record(cursor, record):
                inserted += 1
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
    return inserted, updated


# Kiểm tra đối soát toàn diện tính toàn vẹn dữ liệu trong CSDL SQL Server (Reconciliation)
def verify_database(connection: Any, records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if records is None:
        records = load_processed_records()

    cursor = connection.cursor()
    errors: list[str] = []

    # 1. Đếm số bản ghi trong dbo.Articles và dbo.ArticleFeatures
    cursor.execute("SELECT COUNT(*) FROM dbo.Articles")
    articles_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dbo.ArticleFeatures")
    features_count = cursor.fetchone()[0]

    if articles_count != len(records):
        errors.append(f"Số lượng bản ghi dbo.Articles ({articles_count}) không khớp với file xử lý ({len(records)})")
    if features_count != len(records):
        errors.append(f"Số lượng bản ghi dbo.ArticleFeatures ({features_count}) không khớp với file xử lý ({len(records)})")

    # 2. Kiểm tra tính toàn vẹn của mã article_id
    cursor.execute("SELECT article_id FROM dbo.Articles")
    db_ids = {row[0] for row in cursor.fetchall()}
    file_ids = {r["article_id"] for r in records}
    missing_ids = file_ids - db_ids
    if missing_ids:
        errors.append(f"Thiếu các mã article_id trong CSDL: {list(missing_ids)[:5]}")

    # 3. Kiểm tra khóa ngoại mồ côi (Orphaned Foreign Keys)
    cursor.execute("SELECT COUNT(*) FROM dbo.Articles WHERE category_id NOT IN (SELECT category_id FROM dbo.Categories)")
    if cursor.fetchone()[0] > 0:
        errors.append("Phát hiện khóa ngoại mồ côi: Articles.category_id không tồn tại trong dbo.Categories")

    cursor.execute("SELECT COUNT(*) FROM dbo.Articles WHERE subcategory_id IS NOT NULL AND subcategory_id NOT IN (SELECT subcategory_id FROM dbo.Subcategories)")
    if cursor.fetchone()[0] > 0:
        errors.append("Phát hiện khóa ngoại mồ côi: Articles.subcategory_id không tồn tại trong dbo.Subcategories")

    cursor.execute("SELECT COUNT(*) FROM dbo.Articles WHERE author_id IS NOT NULL AND author_id NOT IN (SELECT author_id FROM dbo.Authors)")
    if cursor.fetchone()[0] > 0:
        errors.append("Phát hiện khóa ngoại mồ côi: Articles.author_id không tồn tại trong dbo.Authors")

    # 4. Kiểm tra 13 đặc trưng mô tả trong dbo.ArticleFeatures không bị rỗng
    cursor.execute("SELECT COUNT(*) FROM dbo.ArticleFeatures WHERE word_count IS NULL OR sentence_count IS NULL OR char_count IS NULL")
    if cursor.fetchone()[0] > 0:
        errors.append("Phát hiện bản ghi trong dbo.ArticleFeatures bị NULL ở các đặc trưng mô tả cốt lõi")

    # 5. Thống kê số lượng các bảng chiều
    cursor.execute("SELECT COUNT(*) FROM dbo.Categories")
    categories_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dbo.Subcategories")
    subcategories_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dbo.Authors")
    authors_count = cursor.fetchone()[0]

    cursor.close()

    result = "PASS" if not errors else "FAIL"
    return {
        "result": result,
        "articles_count": articles_count,
        "features_count": features_count,
        "categories_count": categories_count,
        "subcategories_count": subcategories_count,
        "authors_count": authors_count,
        "expected_records": len(records),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="ADY201m — Microsoft SQL Server Database Runner (Phase L - Load)")
    parser.add_argument("--init-schema", action="store_true", help="Tạo cấu trúc 5 bảng chuẩn 3NF và chỉ mục")
    parser.add_argument("--import", dest="do_import", action="store_true", help="Nạp các bản ghi mới chưa có trong CSDL")
    parser.add_argument("--update", dest="do_update", action="store_true", help="Cập nhật các bản ghi đã tồn tại trong CSDL")
    parser.add_argument("--sync", action="store_true", help="Đồng bộ toàn diện (update-then-insert) và tự kiểm định")
    parser.add_argument("--check", "--verify", dest="do_check", action="store_true", help="Chỉ kiểm định đối soát dữ liệu trong CSDL")
    args = parser.parse_args()

    if not any((args.init_schema, args.do_import, args.do_update, args.sync, args.do_check)):
        parser.error("Cần chọn ít nhất một tác vụ: --init-schema, --import, --update, --sync hoặc --check")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    connection = get_connection()
    records = load_processed_records()
    stats = {"records_loaded": len(records), "schema_batches": 0, "inserted": 0, "updated": 0, "skipped": 0}

    try:
        cursor = connection.cursor()
        if args.init_schema or args.sync:
            stats["schema_batches"] = execute_schema(cursor)
            connection.commit()

        if args.do_import:
            for record in records:
                if import_record(cursor, record):
                    stats["inserted"] += 1
                else:
                    stats["skipped"] += 1
            connection.commit()

        if args.do_update:
            for record in records:
                if update_record(cursor, record):
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1
            connection.commit()

        if args.sync:
            for record in records:
                if update_record(cursor, record):
                    stats["updated"] += 1
                elif import_record(cursor, record):
                    stats["inserted"] += 1
            connection.commit()

        cursor.close()

        # Tự động đối soát dữ liệu (Reconciliation) sau khi sync / import / check
        validation = verify_database(connection, records)
        stats["validation"] = validation

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    DATABASE_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "phase": "Phase L — Microsoft SQL Server 3NF Database Persistence",
        "database_engine": "Microsoft SQL Server",
        "database_name": os.getenv("ADY_SQLSERVER_DATABASE", "ADY201m"),
        "status": "PASS" if stats.get("validation", {}).get("result") == "PASS" else "FAIL",
        "input": str(PROCESSED_JSONL.relative_to(ROOT)).replace("\\", "/"),
        "schema_file": str(SCHEMA_SQL.relative_to(ROOT)).replace("\\", "/"),
        "update_query": str(UPSERT_SQL.relative_to(ROOT)).replace("\\", "/"),
        "records_available": len(records),
        "operations": stats,
    }
    DATABASE_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_md = f"""# ADY201m — Báo cáo Nạp & Đồng bộ CSDL SQL Server 3NF (Phase L)

- **Trạng thái:** **{manifest['status']}**
- **CSDL mục tiêu:** `{manifest['database_name']}`
- **Số bản ghi trong tệp xử lý:** {len(records)}
- **Số bài viết trong CSDL:** {stats.get('validation', {}).get('articles_count', 0)}
- **Số bản ghi đặc trưng (13 đặc trưng):** {stats.get('validation', {}).get('features_count', 0)}
- **Bảng chiều:** {stats.get('validation', {}).get('categories_count', 0)} Categories, {stats.get('validation', {}).get('subcategories_count', 0)} Subcategories, {stats.get('validation', {}).get('authors_count', 0)} Authors
- **Thao tác:** {stats.get('inserted', 0)} inserted, {stats.get('updated', 0)} updated
"""
    DATABASE_SUMMARY.write_text(summary_md, encoding="utf-8")

    val_res = stats.get("validation", {}).get("result", "UNKNOWN")
    print(f"Đồng bộ CSDL hoàn tất: {val_res} ({stats.get('inserted', 0)} inserted, {stats.get('updated', 0)} updated)")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0 if val_res == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
