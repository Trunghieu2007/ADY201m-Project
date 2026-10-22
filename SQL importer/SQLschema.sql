-- =======================================================
-- SCRIPT KHỞI TẠO BẢNG DỮ LIỆU BÁO CHÍ TRÊN MICROSOFT SQL SERVER
-- Bạn có thể mở file này trong SSMS (SQL Server Management Studio) và bấm Execute (F5)
-- =======================================================

-- 1. Tạo Database nếu chưa có (Mặc định dùng ADY201m)
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'ADY201m')
BEGIN
    CREATE DATABASE ADY201m;
    PRINT N'Đã tạo Database ADY201m thành công.';
END
GO

USE ADY201m;
GO

-- 2. Tạo bảng lưu trữ 9 trường dữ liệu bóc tách từ VnExpress
IF OBJECT_ID(N'dbo.VnExpress_Articles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.VnExpress_Articles (
        article_id      NVARCHAR(50)   NOT NULL CONSTRAINT PK_VnExpress_Articles PRIMARY KEY,
        title           NVARCHAR(1000) NOT NULL,
        description     NVARCHAR(MAX)  NULL,
        content         NVARCHAR(MAX)  NULL,
        author          NVARCHAR(255)  NULL,
        published_at    DATETIME       NULL,
        category        NVARCHAR(100)  NULL,
        subcategory     NVARCHAR(100)  NULL,
        url             NVARCHAR(1000) NULL,
        created_at      DATETIME       NOT NULL CONSTRAINT DF_Articles_CreatedAt DEFAULT GETDATE()
    );

    -- Tạo Index hỗ trợ truy vấn nhanh theo chuyên mục cho bước EDA
    CREATE INDEX IX_Articles_Category ON dbo.VnExpress_Articles(category);

    PRINT N'Đã tạo bảng dbo.VnExpress_Articles thành công!';
END
ELSE
BEGIN
    PRINT N'Bảng dbo.VnExpress_Articles đã tồn tại sẵn sàng.';
END
GO
