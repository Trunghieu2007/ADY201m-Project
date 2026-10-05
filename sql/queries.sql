/* ADY201m Phase 6 — analysis/query examples */

-- 1. Article count by category
SELECT c.name AS category, COUNT(*) AS article_count
FROM dbo.Articles a
JOIN dbo.Categories c ON c.category_id = a.category_id
GROUP BY c.name
ORDER BY article_count DESC, category;

-- 2. Recent articles
SELECT TOP (20)
    a.article_id, a.title, c.name AS category, au.name AS author, a.published_at
FROM dbo.Articles a
JOIN dbo.Categories c ON c.category_id = a.category_id
LEFT JOIN dbo.Authors au ON au.author_id = a.author_id
ORDER BY a.published_at DESC;

-- 3. Average text length by category
SELECT
    c.name AS category,
    AVG(CAST(f.word_count AS FLOAT)) AS avg_words,
    AVG(CAST(f.sentence_count AS FLOAT)) AS avg_sentences
FROM dbo.Articles a
JOIN dbo.Categories c ON c.category_id = a.category_id
JOIN dbo.ArticleFeatures f ON f.article_id = a.article_id
GROUP BY c.name
ORDER BY avg_words DESC;

-- 4. Most frequent authors
SELECT TOP (10)
    au.name AS author,
    COUNT(*) AS article_count
FROM dbo.Articles a
JOIN dbo.Authors au ON au.author_id = a.author_id
GROUP BY au.name
ORDER BY article_count DESC, author;

-- 5. Time distribution by publication date
SELECT
    CAST(a.published_at AS DATE) AS publication_date,
    COUNT(*) AS article_count
FROM dbo.Articles a
GROUP BY CAST(a.published_at AS DATE)
ORDER BY publication_date;

-- 6. Window Function: Bài viết mới nhất theo từng chuyên mục (ROW_NUMBER)
SELECT c.name AS category, a.title, a.published_at,
       ROW_NUMBER() OVER (PARTITION BY a.category_id ORDER BY a.published_at DESC) AS rank_in_cat
FROM dbo.Articles a
JOIN dbo.Categories c ON c.category_id = a.category_id;

-- 7. Explicit update example: change the publisher for one article
UPDATE dbo.Articles
SET publisher = N'VnExpress',
    updated_at = SYSUTCDATETIME()
WHERE article_id = ?;
