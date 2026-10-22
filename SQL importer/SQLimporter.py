import os
import sys
import json
from datetime import datetime
# pyrefly: ignore[missing-import]
import pyodbc  # type: ignore

# Hỗ trợ hiển thị tiếng Việt trên terminal Windows
sys.stdout.reconfigure(encoding="utf-8")

SERVER = ".\\SQLEXPRESS"
DATABASE = "ADY201m"
DRIVER = "{ODBC Driver 17 for SQL Server}"

#Chuỗi kết nối: master (để kiểm tra DB) và trực tiếp ADY201m (để nạp liệu)
MASTER_CONN = f"DRIVER={DRIVER};SERVER={SERVER};DATABASE=master;Trusted_Connection=yes;"
DB_CONN = f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;"

SCHEMA_HINT = (
    "  -> Hãy chạy file 'SQL importer/SQLschema.sql' trong SSMS để khởi tạo "
    "Database ADY201m và bảng dbo.VnExpress_Articles trước khi nạp dữ liệu."
)

#Ép chuỗi ngày 'YYYY-MM-DD HH:MM:SS' (từ crawler) về datetime để ghi cột DATETIME
def to_datetime(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

#Kiểm tra Database ADY201m tồn tại qua kết nối master; trả về True/False
def database_exists():
    conn = pyodbc.connect(MASTER_CONN, autocommit=True)
    cursor = conn.cursor()
    cursor.execute("SELECT database_id FROM sys.databases WHERE name = ?", DATABASE)
    found = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return found

#Kiểm tra bảng dbo.VnExpress_Articles đã tồn tại trong ADY201m hay chưa
def table_exists(cursor):
    cursor.execute("SELECT OBJECT_ID(N'dbo.VnExpress_Articles', N'U')")
    return cursor.fetchone()[0] is not None

#Đọc JSON, lọc trùng (trong batch và với CSDL) rồi nạp vào SQL Server qua executemany
def import_json_to_sql(json_path=None):
    candidates = [
        "Web crawler/vnexpress_data.json", "../Web crawler/vnexpress_data.json",
        "Crawler/vnexpress_data.json", "../Crawler/vnexpress_data.json",
        "vnexpress_data.json"
    ]
    path = json_path or next((c for c in candidates if os.path.exists(c)), "Web crawler/vnexpress_data.json")
    if not os.path.exists(path):
        print(f"[!] Không tìm thấy file dữ liệu: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # Bước 1: Kiểm tra Database qua master. Không tự tạo -> yêu cầu user chạy schema.
    if not database_exists():
        print(f"[!] Database '{DATABASE}' chưa tồn tại trên {SERVER}." + SCHEMA_HINT)
        return

    conn = pyodbc.connect(DB_CONN, autocommit=True)
    cursor = conn.cursor()

    # Bước 2: Kiểm tra bảng. Không tự tạo -> báo user nạp schema (giảm codebase).
    if not table_exists(cursor):
        print(f"[!] Bảng 'dbo.VnExpress_Articles' chưa tồn tại trong '{DATABASE}'." + SCHEMA_HINT)
        cursor.close()
        conn.close()
        return

    # Bước 3a: Lọc trùng NGAY TRONG BATCH theo article_id (tránh vi phạm PRIMARY KEY)
    seen = set()
    batch_unique = []
    for a in articles:
        aid = a.get("article_id")
        if aid and aid not in seen:
            seen.add(aid)
            batch_unique.append(a)

    # Bước 3b: Lọc với các article_id đã có trong CSDL
    cursor.execute("SELECT article_id FROM dbo.VnExpress_Articles")
    existing_ids = {row[0] for row in cursor.fetchall()}
    new_articles = [a for a in batch_unique if a["article_id"] not in existing_ids]

    insert_sql = """
    INSERT INTO dbo.VnExpress_Articles
    (article_id, title, description, content, author, published_at, category, subcategory, url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    def to_params(a):
        return (
            a.get("article_id"), a.get("title"), a.get("description"),
            a.get("content"), a.get("author"), to_datetime(a.get("published_at")),
            a.get("category"), a.get("subcategory"), a.get("url"),
        )

    inserted, failed = 0, []
    try:
        cursor.fast_executemany = True
        cursor.executemany(insert_sql, [to_params(a) for a in new_articles])
        inserted = len(new_articles)
    except pyodbc.Error as bulk_err:
        # Fallback: chèn từng dòng để 1 dòng lỗi không phá hỏng cả batch
        cursor.fast_executemany = False
        print(f"[!] executemany lỗi ({bulk_err}); chuyển sang chèn từng dòng...")
        for a in new_articles:
            try:
                cursor.execute(insert_sql, to_params(a))
                inserted += 1
            except pyodbc.Error as e:
                failed.append((a.get("article_id"), str(e).strip()))

    cursor.close()
    conn.close()

    skipped = len(articles) - len(new_articles)
    print(f"[+] Hoàn tất! Đã thêm mới: {inserted} bài | Bỏ qua trùng lặp: {skipped} bài.")
    if failed:
        print(f"[!] {len(failed)} bài thất bại (chi tiết dưới):")
        for aid, err in failed:
            print(f"     - {aid}: {err}")

if __name__ == "__main__":
    # Khởi chạy import dữ liệu JSON vào SQL Server khi thực thi trực tiếp file
    import_json_to_sql()
