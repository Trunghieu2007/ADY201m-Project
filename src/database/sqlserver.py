from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_SQL = ROOT / "sql" / "create_tables.sql"
QUERIES_SQL = ROOT / "sql" / "queries.sql"
UPSERT_SQL = ROOT / "sql" / "upsert_article.sql"
PROCESSED_JSONL = ROOT / "data" / "processed" / "articles_processed.jsonl"

FEATURE_COLUMNS = (
    "char_count", "word_count", "sentence_count", "unique_word_count",
    "lexical_diversity", "avg_word_length", "title_char_count", "title_word_count",
    "description_char_count", "description_word_count", "title_to_content_word_ratio",
    "publication_hour", "publication_weekday",
)


# Xây dựng chuỗi kết nối Microsoft SQL Server từ biến môi trường
def build_connection_string() -> str:
    explicit = os.getenv("ADY_SQLSERVER_CONNECTION_STRING")
    if explicit:
        return explicit
    driver = os.getenv("ADY_SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server")
    server = os.getenv("ADY_SQLSERVER_SERVER", "localhost")
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
    return pyodbc.connect(build_connection_string(), autocommit=False)


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
    author_id = ensure_dimension(cursor, "Authors", record["author"]) if record.get("author") else None

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
    author_id = ensure_dimension(cursor, "Authors", record["author"]) if record.get("author") else None

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
