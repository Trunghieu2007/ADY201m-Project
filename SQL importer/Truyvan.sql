USE ADY201m;

-- Xem 10 bài mới nhất vừa nạp vào
SELECT TOP 10 article_id, title, category, published_at, author 
FROM dbo.VnExpress_Articles 
ORDER BY published_at DESC;

-- Đếm tổng số bài đã tích lũy trong CSDL
SELECT COUNT(*) AS TongSoBai FROM dbo.VnExpress_Articles;

-- Xem số lượng bài theo từng chuyên mục:
SELECT category, COUNT(*) AS SoLuong
FROM dbo.VnExpress_Articles
GROUP BY category
ORDER BY SoLuong DESC;

-- Xem các bài thuộc chuyên mục Thể thao:
SELECT title, published_at, url 
FROM dbo.VnExpress_Articles 
WHERE category = N'Thể thao';

-- Kiểm tra bài viết dài nhất:
SELECT TOP 5 title, LEN(content) AS DoDaiNoiDung 
FROM dbo.VnExpress_Articles 
ORDER BY LEN(content) DESC;