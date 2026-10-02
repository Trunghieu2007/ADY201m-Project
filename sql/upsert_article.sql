/* Parameter contract used by src/database/sqlserver.py.
   The Python implementation deliberately uses separate UPDATE/INSERT statements
   so the data path is easy to explain and audit. */

-- UPDATE existing article
UPDATE dbo.Articles
SET url = ?,
    title = ?,
    description = ?,
    content = ?,
    author_id = ?,
    publisher = ?,
    published_at = ?,
    category_id = ?,
    subcategory_id = ?,
    crawled_at = ?,
    source = ?,
    updated_at = SYSUTCDATETIME()
WHERE article_id = ?;

-- INSERT is executed only when UPDATE found no row.
INSERT INTO dbo.Articles(
    article_id, url, title, description, content, author_id, publisher,
    published_at, category_id, subcategory_id, crawled_at, source
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
