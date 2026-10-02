/* ADY201m Phase 6 — Microsoft SQL Server schema.
   Run this against the target database (for example ADY201m). */

IF OBJECT_ID(N'dbo.Categories', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Categories (
        category_id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Categories PRIMARY KEY,
        name NVARCHAR(100) NOT NULL CONSTRAINT UQ_Categories_Name UNIQUE
    );
END
GO

IF OBJECT_ID(N'dbo.Subcategories', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Subcategories (
        subcategory_id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Subcategories PRIMARY KEY,
        category_id INT NOT NULL,
        name NVARCHAR(100) NOT NULL,
        CONSTRAINT FK_Subcategories_Categories FOREIGN KEY (category_id)
            REFERENCES dbo.Categories(category_id),
        CONSTRAINT UQ_Subcategories_Category_Name UNIQUE(category_id, name)
    );
END
GO

IF OBJECT_ID(N'dbo.Authors', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Authors (
        author_id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Authors PRIMARY KEY,
        name NVARCHAR(255) NOT NULL CONSTRAINT UQ_Authors_Name UNIQUE
    );
END
GO

IF OBJECT_ID(N'dbo.Articles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Articles (
        article_id NVARCHAR(50) NOT NULL CONSTRAINT PK_Articles PRIMARY KEY,
        url NVARCHAR(1000) NOT NULL CONSTRAINT UQ_Articles_Url UNIQUE,
        title NVARCHAR(1000) NOT NULL,
        description NVARCHAR(MAX) NULL,
        content NVARCHAR(MAX) NULL,
        author_id INT NULL,
        publisher NVARCHAR(255) NULL,
        published_at DATETIMEOFFSET(0) NULL,
        category_id INT NOT NULL,
        subcategory_id INT NULL,
        crawled_at DATETIMEOFFSET(0) NULL,
        source NVARCHAR(100) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_Articles_CreatedAt DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(0) NOT NULL CONSTRAINT DF_Articles_UpdatedAt DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_Articles_Authors FOREIGN KEY (author_id) REFERENCES dbo.Authors(author_id),
        CONSTRAINT FK_Articles_Categories FOREIGN KEY (category_id) REFERENCES dbo.Categories(category_id),
        CONSTRAINT FK_Articles_Subcategories FOREIGN KEY (subcategory_id) REFERENCES dbo.Subcategories(subcategory_id)
    );
END
GO

IF OBJECT_ID(N'dbo.ArticleFeatures', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ArticleFeatures (
        article_id NVARCHAR(50) NOT NULL CONSTRAINT PK_ArticleFeatures PRIMARY KEY,
        char_count INT NULL,
        word_count INT NULL,
        sentence_count INT NULL,
        unique_word_count INT NULL,
        lexical_diversity FLOAT NULL,
        avg_word_length FLOAT NULL,
        title_char_count INT NULL,
        title_word_count INT NULL,
        description_char_count INT NULL,
        description_word_count INT NULL,
        title_to_content_word_ratio FLOAT NULL,
        publication_hour INT NULL,
        publication_weekday INT NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_ArticleFeatures_CreatedAt DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(0) NOT NULL CONSTRAINT DF_ArticleFeatures_UpdatedAt DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_ArticleFeatures_Articles FOREIGN KEY (article_id) REFERENCES dbo.Articles(article_id)
    );
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Articles_Category' AND object_id = OBJECT_ID(N'dbo.Articles'))
    CREATE INDEX IX_Articles_Category ON dbo.Articles(category_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Articles_PublishedAt' AND object_id = OBJECT_ID(N'dbo.Articles'))
    CREATE INDEX IX_Articles_PublishedAt ON dbo.Articles(published_at);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Articles_Author' AND object_id = OBJECT_ID(N'dbo.Articles'))
    CREATE INDEX IX_Articles_Author ON dbo.Articles(author_id);
GO
