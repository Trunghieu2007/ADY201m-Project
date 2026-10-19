import os
import sys
import json
# pyrefly: ignore[missing-import]
import pyodbc  # type: ignore

# Hỗ trợ hiển thị tiếng Việt trên terminal Windows
sys.stdout.reconfigure(encoding="utf-8")

#Chuỗi kết nối cơ sở dữ liệu SQL Server
CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=.\\SQLEXPRESS;"
    "DATABASE=ADY201m;"
    "Trusted_Connection=yes;"
)

#Tạo bảng dbo.VnExpress_Articles và index nếu chưa tồn tại trong CSDL
def init_table(cursor):
    cursor.execute("""
    IF OBJECT_ID(N'dbo.VnExpress_Articles', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.VnExpress_Articles (
            article_id   NVARCHAR(50)   NOT NULL PRIMARY KEY,
            title        NVARCHAR(1000) NOT NULL,
            description  NVARCHAR(MAX)  NULL,
            content      NVARCHAR(MAX)  NULL,
            author       NVARCHAR(255)  NULL,
            published_at NVARCHAR(255)  NULL,
            category     NVARCHAR(100)  NULL,
            subcategory  NVARCHAR(100)  NULL,
            url          NVARCHAR(1000) NULL,
            created_at   DATETIME       NOT NULL DEFAULT GETDATE()
        );
        CREATE INDEX IX_Articles_Category ON dbo.VnExpress_Articles(category);
    END
    """)

#Đọc dữ liệu từ file JSON, lọc các bản ghi trùng lặp và chèn vào SQL Server
def import_json_to_sql(json_path=None):
    # Tự động tìm file json theo các thư mục hiện tại
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

    conn = pyodbc.connect(CONN_STR, autocommit=True)
    cursor = conn.cursor()
    init_table(cursor)

    # Lấy danh sách ID đã có để lọc trùng siêu nhanh
    cursor.execute("SELECT article_id FROM dbo.VnExpress_Articles")
    existing_ids = {row[0] for row in cursor.fetchall()}

    insert_sql = """
    INSERT INTO dbo.VnExpress_Articles 
    (article_id, title, description, content, author, published_at, category, subcategory, url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    new_articles = [a for a in articles if a.get("article_id") not in existing_ids]

    for a in new_articles:
        cursor.execute(insert_sql, (
            a.get("article_id"), a.get("title"), a.get("description"),
            a.get("content"), a.get("author"), a.get("published_at"),
            a.get("category"), a.get("subcategory"), a.get("url")
        ))

    cursor.close()
    conn.close()

    skipped = len(articles) - len(new_articles)
    print(f"[+] Hoàn tất! Đã thêm mới: {len(new_articles)} bài | Bỏ qua trùng lặp: {skipped} bài.")

if __name__ == "__main__":
    #Khởi chạy import dữ liệu JSON vào SQL Server khi thực thi trực tiếp file
    import_json_to_sql()
