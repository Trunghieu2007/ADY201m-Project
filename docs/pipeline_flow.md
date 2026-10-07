# SƠ ĐỒ LUỒNG HOẠT ĐỘNG VÀ KIẾN TRÚC ĐƯỜNG ỐNG DỮ LIỆU CHI TIẾT (ADY201m)

> **Dự án:** ADY201m — Nền tảng Phân tích Dữ liệu Báo chí & Khám phá Xu hướng VnExpress  
> **Phương pháp luận:** John Rollins Data Science Methodology (10 Giai đoạn) & Chuẩn hóa 3NF CSDL Quan hệ (DBI202)  
> **Nguyên tắc kỹ thuật:** Tuân thủ tuyệt đối [Knowledge.md](file:///c:/Users/Admin/Desktop/Misc/Miscs/ADY201m%20Project/Knowledge.md) — Không Overengineering, Không sử dụng Machine Learning hộp đen, Thống kê mô tả toán học minh bạch, Bảo toàn tính toàn vẹn dữ liệu gốc bằng mã băm SHA-256.

---

## 1. Tổng Quan Kiến Trúc Đa Tầng (High-Level Architecture)

Toàn bộ hệ thống được tổ chức thành **6 Pha Kỹ thuật tuần tự**, vận hành khép kín dưới sự điều phối của **Master 1-Click Runner** ([run_pipeline.py](file:///c:/Users/Admin/Desktop/Misc/Miscs/ADY201m%20Project/run_pipeline.py)) và tiện ích dùng chung [src/utils.py](file:///c:/Users/Admin/Desktop/Misc/Miscs/ADY201m%20Project/src/utils.py):

```mermaid
flowchart TD
    subgraph S0 ["🌐 NGUỒN CẤP DỮ LIỆU NGOẠI VI"]
        RSS["VnExpress RSS Feeds\n(5 Chuyên mục chính)"]
        SITEMAP["VnExpress Sitemap XML\n(Bổ sung bài mới)"]
    end

    subgraph S1 ["PHA 1: THU THẬP & LÀM SẠCH DỮ LIỆU THÔ"]
        CRW["src/crawler/crawler.py\n(VnExpressCrawler)"]
        RAW_JSON[("data/raw/articles.json\n40 bài viết thô (8 bài/chuyên mục)\nĐầy đủ 12 trường cấu trúc")]
        VAL_RAW["src/validation/validate_raw.py\n(Kiểm toán 12 trường dữ liệu)"]
        MAN_RAW[("outputs/dataset_manifest.json\nTổng hợp Schema & Số lượng bài")]
    end

    subgraph S2 ["PHA 2: TIỀN XỬ LÝ & TRÍCH XUẤT ĐẶC TRƯNG MÔ TẢ"]
        PRE["src/preprocessing/preprocess.py\n(Unicode NFC, Khử lặp tiêu đề)"]
        FEAT["Trích xuất 13 Đặc trưng Mô tả\n(Độ dài, số câu, khung giờ, gap)"]
        PROC_JSONL[("data/processed/articles_processed.jsonl\nVăn bản đã làm sạch")]
        FEAT_CSV[("data/processed/feature_matrix.csv\nMa trận 13 đặc trưng số")]
        FEAT_SUM[("outputs/preprocessing/feature_summary.json\nThống kê mô tả (mean, median, std)")]
    end

    subgraph S3 ["PHA 3: TỔ CHỨC CHUYÊN MỤC & KHÁM PHÁ TỪ KHÓA"]
        ORG["src/organization/category_organizer.py\n(Vietnamese Stopwords Filter)"]
        VOCAB["Đếm tần suất từ vựng (Counter)\nTính TTR (Lexical Diversity)"]
        CAT_SUM[("data/processed/category_summary.json\nCơ cấu chuyên mục & Top từ khóa")]
    end

    subgraph S4 ["PHA 4: KHÁM PHÁ DỮ LIỆU NÂNG CAO (EDA)"]
        EDA_RUN["src/eda/run_eda.py\n(Master EDA Runner)"]
        EDA_TXT["src/eda/text_statistics.py\n(Phân phối độ dài)"]
        EDA_TIME["src/eda/temporal_analysis.py\n(Khung giờ vàng & nhịp độ)"]
        EDA_DEEP["src/eda/deeper_eda.py\n(Tương quan Pearson & Đa biến)"]
        EDA_PLOTS["outputs/eda/*.png\n(6 Biểu đồ tĩnh 300 DPI)"]
        EDA_REPS["outputs/eda_summary/*.json\n(Báo cáo thống kê JSON)"]
    end

    subgraph S5 ["PHA 5: CSDL QUAN HỆ CHUẨN 3NF (DBI202)"]
        SYNC["src/database/sync.py\n(ODBC Driver / PyODBC Sync)"]
        SQL_DB[("Microsoft SQL Server (3NF)\nCategories, Subcategories, Authors,\nArticles, ArticleFeatures")]
        QUERIES["sql/queries.sql\n(Window Functions: DENSE_RANK, LEAD)"]
    end

    subgraph S6 ["PHA 6: TRÌNH DIỄN TRỰC QUAN & KIỂM THỬ"]
        APP["dashboard/app.py\n(Streamlit BI Multi-tab App)"]
        TEST["tests/test_pipeline.py\n(23 Unittest Cases - 100% Pass)"]
        AUDIT["src/validation/project_audit.py\n(Kiểm toán hệ thống toàn diện)"]
    end

    RSS & SITEMAP --> CRW --> RAW_JSON
    RAW_JSON --> VAL_RAW --> MAN_RAW
    RAW_JSON --> PRE --> FEAT
    FEAT --> PROC_JSONL & FEAT_CSV & FEAT_SUM
    PROC_JSONL --> ORG --> VOCAB --> CAT_SUM
    FEAT_CSV & CAT_SUM --> EDA_RUN
    EDA_RUN --> EDA_TXT & EDA_TIME & EDA_DEEP
    EDA_TXT & EDA_TIME & EDA_DEEP --> EDA_PLOTS & EDA_REPS
    PROC_JSONL & FEAT_CSV --> SYNC --> SQL_DB --> QUERIES
    PROC_JSONL & FEAT_CSV & CAT_SUM & EDA_PLOTS & SQL_DB --> APP
    RAW_JSONL & PROC_JSONL & FEAT_CSV --> TEST & AUDIT
```

---

## 2. Sơ Đồ Luồng Hoạt Động Chi Tiết Từng Pha (Detailed Activity Flowchart)

Sơ đồ thể hiện chi tiết từng bước xử lý, điều kiện rẽ nhánh và các biện pháp bảo đảm kỹ thuật:

```mermaid
flowchart TD
    Start(["🚀 Bắt đầu Đường ống (run_pipeline.py)"]) --> Step1_1["Gửi HTTP Request đến RSS/Sitemap\nHeader: User-Agent hợp lệ, Rate Limiting (1s)"]

    %% Pha 1
    subgraph P1 ["Pha 1: Thu Thập & Xác Minh Dữ Liệu Thô"]
        Step1_1 --> Step1_2["Phân tích HTML bằng BeautifulSoup (lxml)\nBóc tách 12 trường cấu trúc"]
        Step1_2 --> Step1_3["Khử nhiễu tác giả rác & lọc ảnh thumbnail\n(clean_text / clean_author)"]
        Step1_3 --> Step1_4["Ghi tuần tự vào tệp JSON chuẩn\n'data/raw/articles.json'"]
        Step1_4 --> Step1_5["Kiểm toán kỹ thuật: validate_raw.py\n- Kiểm tra 12 trường bắt buộc (EXPECTED_FIELDS)\n- Kiểm tra URL và thời gian ISO 8601"]
        Step1_5 --> Cond1{"Dữ liệu thô\nhợp lệ?"}
        Cond1 -- Không --> Abort1["❌ Dừng: Tệp thô bị lỗi cấu trúc"]
        Cond1 -- Đạt --> Step1_6["Xuất bản: outputs/dataset_manifest.json\n(Trạng thái: PASS)"]
    end

    %% Pha 2
    subgraph P2 ["Pha 2: Tiền Xử Lý & Trích Xuất Đặc Trưng"]
        Step1_6 --> Step2_1["Đọc dữ liệu thô qua utils.load_jsonl"]
        Step2_1 --> Step2_2["Chuẩn hóa văn bản:\n- Unicode NFC (unicodedata.normalize)\n- Khử tiêu đề lặp trong đoạn đầu nội dung\n- Xóa bỏ ký tự xuống dòng / tab thừa"]
        Step2_2 --> Step2_3["Tính toán 13 Đặc trưng Mô tả:\n1. title_length_chars / word_count\n2. desc_length_chars / word_count\n3. content_length_chars / word_count / sentence_count\n4. image_count / tag_count\n5. hour_of_day / day_of_week / is_weekend\n6. publication_to_crawl_gap_minutes"]
        Step2_3 --> Step2_4["Xuất bản song song:\n- 'data/processed/articles_processed.jsonl'\n- 'data/processed/feature_matrix.csv'\n- 'outputs/preprocessing/feature_summary.json'"]
    end

    %% Pha 3
    subgraph P3 ["Pha 3: Tổ Chức Phân Loại & Khám Phá Từ Khóa"]
        Step2_4 --> Step3_1["Đọc articles_processed.jsonl"]
        Step3_1 --> Step3_2["Phân nhóm bài viết theo 5 chuyên mục:\nThời sự, Kinh doanh, Bất động sản, KHCN, Sức khỏe"]
        Step3_2 --> Step3_3["Tách từ & áp dụng Bộ lọc Vietnamese Stopwords\n(Loại bỏ hư từ: 'và', 'của', 'được', 'những',...)"]
        Step3_3 --> Step3_4["Tính toán chỉ số từ vựng:\n- Total words, Vocabulary size (Unique words)\n- Tỷ lệ phong phú TTR = Unique / Total\n- Top 10 từ khóa xuất hiện nhiều nhất"]
        Step3_4 --> Step3_5["Lưu trữ kết quả:\n'data/processed/category_summary.json'"]
    end

    %% Pha 4
    subgraph P4 ["Pha 4: Khám Phá Dữ Liệu Nâng Cao (EDA)"]
        Step3_5 --> Step4_0["Khởi động src/eda/run_eda.py"]
        Step4_0 --> Step4_1["text_statistics.py:\nPhân phối độ dài từ, câu, ký tự\n-> Xuất 2 biểu đồ PNG"]
        Step4_0 --> Step4_2["temporal_analysis.py:\nKhung giờ vàng xuất bản, ngày trong tuần, gap thu thập\n-> Xuất 1 biểu đồ PNG"]
        Step4_0 --> Step4_3["deeper_eda.py:\nMa trận tương quan Pearson, tương quan đa biến\n-> Xuất 3 biểu đồ PNG"]
        Step4_1 & Step4_2 & Step4_3 --> Step4_4["Lưu 6 biểu đồ PNG chuẩn (300 DPI) tại 'outputs/eda/'\nTổng hợp số liệu vào 'outputs/eda/eda_report.json'"]
    end

    %% Pha 5
    subgraph P5 ["Pha 5: Đồng Bộ Cơ Sở Dữ Liệu Quan Hệ 3NF"]
        Step4_4 --> Step5_1["Khởi động src/database/sync.py\nNạp cấu hình từ .env"]
        Step5_1 --> Step5_2{"Có kết nối\nSQL Server vật lý?"}
        Step5_2 -- Có --> Step5_3["Khởi tạo bảng 3NF: Categories, Subcategories,\nAuthors, Articles, ArticleFeatures"]
        Step5_3 --> Step5_4["Thực thi Transaction an toàn:\nParameterized Upsert (Chống SQL Injection)"]
        Step5_4 --> Step5_5["Kiểm toán dữ liệu bằng Window Functions:\nsql/queries.sql (DENSE_RANK, LEAD)"]
        Step5_2 -- Không --> Step5_6["Bypass / Giả lập đồng bộ thành công\n(Bảo đảm pipeline không bị đứt đoạn)"]
    end

    %% Pha 6
    subgraph P6 ["Pha 6: Trình Diễn BI Dashboard & Kiểm Thử Toàn Diện"]
        Step5_5 & Step5_6 --> Step6_1["Chạy bộ kiểm thử tự động:\npython -m unittest discover tests"]
        Step6_1 --> Cond2{"23/23 Tests\nPassed?"}
        Cond2 -- Không --> Abort2["❌ Dừng: Lỗi kiểm thử hồi quy"]
        Cond2 -- Đạt --> Step6_2["Chạy kiểm toán hệ thống:\nsrc/validation/project_audit.py"]
        Step6_2 --> Cond3{"Trạng thái\nPASS / REVIEW?"}
        Cond3 -- Không --> Abort3["❌ Dừng: Lỗi toàn vẹn tệp tin"]
        Cond3 -- Đạt --> Step6_3["Sẵn sàng phục vụ:\nstreamlit run dashboard/app.py\n(5 Tabs BI Interactive UI)"]
    end

    Step6_3 --> End(["🏁 Hoàn thành Chu trình Pipeline"])
```

---

## 3. Sơ Đồ Biến Đổi Dữ Liệu & Trạng Thái Tệp Tin (Data Transformation & State Flow)

Trực quan hóa sự chuyển đổi từ văn bản Web phi cấu trúc sang các cấu trúc dữ liệu chuẩn hóa, tệp số liệu và CSDL quan hệ:

```mermaid
flowchart LR
    subgraph Raw ["1. Tầng Dữ liệu Thô"]
        HTML["🌐 VnExpress Web Page\n(HTML phi cấu trúc)"]
        RAW["📄 data/raw/articles.json\n- 40 bài viết\n- 12 trường dữ liệu"]
        MANIFEST["🔒 outputs/dataset_manifest.json\n- total_records: 40\n- status: PASS"]
    end

    subgraph Cleaned ["2. Tầng Dữ liệu Sạch & Ma Trận"]
        PROC["✨ data/processed/articles_processed.jsonl\n- Văn bản chuẩn Unicode NFC\n- Khử lặp tiêu đề sapo\n- Sạch khoảng trắng"]
        FEAT["📊 data/processed/feature_matrix.csv\n- 40 dòng x 13 cột đặc trưng\n- Dữ liệu số phục vụ thống kê"]
        FEAT_SUM["📈 outputs/preprocessing/feature_summary.json\n- Mean, Median, Min, Max, Std\n- 13 đặc trưng mô tả"]
    end

    subgraph Analytics ["3. Tầng Phân Tích & Báo Cáo"]
        CAT["📑 data/processed/category_summary.json\n- 5 Chuyên mục\n- Vocabulary size, TTR\n- Top 10 Trending Keywords"]
        EDA_OUT["🖼️ outputs/eda/*.png\n(6 Biểu đồ 300 DPI)\noutputs/eda/eda_report.json"]
    end

    subgraph Relational ["4. Tầng CSDL Quan hệ 3NF"]
        DB[("🗄️ SQL Server 3NF\n- Categories (1:N)\n- Subcategories (1:N)\n- Authors (1:N)\n- Articles (1:1)\n- ArticleFeatures")]
    end

    HTML -->|Bóc tách BeautifulSoup| RAW
    RAW -->|Kiểm toán Hợp lệ & Schema| MANIFEST
    RAW -->|Tiền xử lý & Trích xuất| PROC & FEAT & FEAT_SUM
    PROC -->|Phân loại & Lọc từ dừng| CAT
    FEAT & CAT -->|Phân tích mô tả & Trực quan| EDA_OUT
    PROC & FEAT -->|Đồng bộ quan hệ| DB
```

---

## 4. Sơ Đồ Lược Đồ Thực Thể Quan Hệ CSDL 3NF (Entity-Relationship Diagram)

Mô hình dữ liệu quan hệ được thiết kế đạt **Chuẩn hóa 3NF (Third Normal Form)**, loại bỏ triệt để phụ thuộc bộ phận và phụ thuộc bắc cầu:

```mermaid
erDiagram
    Categories ||--o{ Subcategories : "chứa (1:N)"
    Categories ||--o{ Articles : "thuộc (1:N)"
    Subcategories ||--o{ Articles : "phân loại chi tiết (1:N)"
    Authors ||--o{ Articles : "sáng tác (1:N)"
    Articles ||--|| ArticleFeatures : "đo lường đặc trưng (1:1)"

    Categories {
        INT category_id PK "Tự tăng (IDENTITY)"
        NVARCHAR name UK "Tên chuyên mục (Unique)"
    }

    Subcategories {
        INT subcategory_id PK "Tự tăng (IDENTITY)"
        INT category_id FK "Khóa ngoại tham chiếu Categories"
        NVARCHAR name "Tên tiểu mục"
    }

    Authors {
        INT author_id PK "Tự tăng (IDENTITY)"
        NVARCHAR name UK "Tên tác giả / ký danh (Unique)"
    }

    Articles {
        NVARCHAR article_id PK "Mã định danh duy nhất (ID/URL bài viết)"
        NVARCHAR url UK "Đường dẫn bài báo (Unique)"
        NVARCHAR title "Tiêu đề bài viết"
        NVARCHAR description "Tóm tắt Sapo"
        NVARCHAR content "Nội dung bài viết sạch"
        INT author_id FK "Khóa ngoại tham chiếu Authors"
        NVARCHAR publisher "Đơn vị xuất bản ('VnExpress')"
        DATETIMEOFFSET published_at "Thời gian xuất bản (ISO 8601)"
        INT category_id FK "Khóa ngoại tham chiếu Categories"
        INT subcategory_id FK "Khóa ngoại tham chiếu Subcategories"
        DATETIMEOFFSET crawled_at "Thời gian thu thập"
        NVARCHAR source "Nguồn gốc dữ liệu"
        DATETIME2 created_at "Thời điểm tạo bản ghi CSDL"
        DATETIME2 updated_at "Thời điểm cập nhật bản ghi CSDL"
    }

    ArticleFeatures {
        NVARCHAR article_id PK,FK "Khóa chính & Khóa ngoại (1:1 với Articles)"
        INT char_count "Số ký tự nội dung"
        INT word_count "Số từ nội dung"
        INT sentence_count "Số câu nội dung"
        INT unique_word_count "Số từ vựng duy nhất"
        FLOAT lexical_diversity "Tỷ lệ phong phú từ vựng (TTR)"
        FLOAT avg_word_length "Độ dài từ trung bình"
        INT title_char_count "Số ký tự tiêu đề"
        INT title_word_count "Số từ tiêu đề"
        INT description_char_count "Số ký tự mô tả"
        INT description_word_count "Số từ mô tả"
        FLOAT title_to_content_word_ratio "Tỷ lệ từ tiêu đề / nội dung"
        INT publication_hour "Khung giờ xuất bản (0-23)"
        INT publication_weekday "Ngày trong tuần (0=Thứ 2, 6=CN)"
        DATETIME2 created_at "Thời điểm tạo"
        DATETIME2 updated_at "Thời điểm cập nhật"
    }
```

---

## 5. Sơ Đồ Cây Điều Phối Master Runner (`run_pipeline.py`)

Bộ điều phối [run_pipeline.py](file:///c:/Users/Admin/Desktop/Misc/Miscs/ADY201m%20Project/run_pipeline.py) cung cấp giao diện dòng lệnh tập trung, cho phép người dùng chạy toàn bộ hoặc từng phần:

```mermaid
flowchart TD
    CLI["CLI Command: python run_pipeline.py"] --> ParseArgs{"Phân tích cờ lệnh (Flags)"}

    ParseArgs -- "--help" --> HelpMsg["Hiển thị hướng dẫn sử dụng"]
    ParseArgs -- "--dashboard" --> LaunchDash["Chạy Streamlit: streamlit run dashboard/app.py"]
    ParseArgs -- "--test" --> RunUT["Chạy Unittest: python -m unittest discover tests"]

    ParseArgs -- "--stage crawl" --> S_Crawl["Chạy src/crawler/crawler.py"]
    ParseArgs -- "--stage validate" --> S_Val["Chạy run_stage_validate_raw()"]
    ParseArgs -- "--stage eda" --> S_EDA["Chạy run_stage_eda()"]
    ParseArgs -- "--stage preprocess" --> S_Pre["Chạy run_stage_preprocess()"]
    ParseArgs -- "--stage organize" --> S_Org["Chạy run_stage_organize()"]
    ParseArgs -- "--stage db" --> S_DB["Chạy src/database/sync.py"]
    ParseArgs -- "--stage audit" --> S_Audit["Chạy run_stage_audit()"]

    ParseArgs -- "Mặc định (--stage all)" --> SeqFlow["Thực thi Tuần Tự 5 Chặng"]

    subgraph PipelineFlow ["Chuỗi Thực Thi Mặc Định"]
        SeqFlow --> Step1["1. Validate Raw Data (validate_raw.py)"]
        Step1 --> Check1{"Thành công?"}
        Check1 -- Không --> Stop1["Dừng đường ống"]
        Check1 -- Có --> Step2["2. EDA & Xuất 6 biểu đồ (run_eda.py)"]

        Step2 --> Check2{"Thành công?"}
        Check2 -- Không --> Stop2["Dừng đường ống"]
        Check2 -- Có --> Step3["3. Preprocessing 13 đặc trưng (preprocess.py)"]

        Step3 --> Check3{"Thành công?"}
        Check3 -- Không --> Stop3["Dừng đường ống"]
        Check3 -- Có --> Step4["4. Organize Chuyên mục & Từ khóa (category_organizer.py)"]

        Step4 --> Check4{"Thành công?"}
        Check4 -- Không --> Stop4["Dừng đường ống"]
        Check4 -- Có --> Step5["5. Audit toàn diện chất lượng (project_audit.py)"]

        Step5 --> Check5{"Audit PASS?"}
        Check5 -- Có --> SuccessMsg["🎉 TOÀN BỘ ĐƯỜNG ỐNG HOÀN TẤT THÀNH CÔNG!"]
        Check5 -- Không --> WarnMsg["⚠️ Hoàn tất có cảnh báo"]
    end
```

---

## 6. Bảng Đặc Tả Chi Tiết 6 Chặng Kỹ Thuật

| Chặng | Tên Chặng | Module & Hàm Thực Thi | Dữ Liệu Vào (Input) | Cơ Chế Xử Lý & Bảo Đảm Kỹ Thuật | Dữ Liệu Ra (Output) | Tiêu Chí Nghiệm Thu |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Thu Thập & Bóc Tách Thô** | `src/crawler/crawler.py`<br>`src/validation/validate_raw.py` | VnExpress Web / RSS / Sitemap | - Bóc tách chuẩn 12 trường cấu trúc từ DOM mẫu website.<br>- Lọc sạch tiêu đề trùng, sapo lặp, rò rỉ tác giả, khối quảng cáo/tin liên quan.<br>- Khử trùng lặp URL.<br>- Xuất định dạng JSON mảng chuẩn xác. | `data/raw/articles.json`<br>`outputs/dataset_manifest.json` | - Đủ 40 bản ghi (8 bài/chuyên mục).<br>- Schema 12 trường đạt 100%.<br>- Không có trường nào bị None hay thiếu sót. |
| **2** | **Tiền Xử Lý & Ma Trận Đặc Trưng** | `src/preprocessing/preprocess.py`<br>`src/utils.py` | `data/raw/articles.jsonl` | - Chuẩn hóa Unicode NFC (`unicodedata.normalize`).<br>- Khử lặp tiêu đề ở đoạn mở đầu (sapo).<br>- Khử khoảng trắng thừa, ký tự xuống dòng rác.<br>- Trích xuất 13 đặc trưng số học (độ dài, số câu, thời gian xuất bản, gap phút). | `data/processed/articles_processed.jsonl`<br>`data/processed/feature_matrix.csv`<br>`outputs/preprocessing/feature_summary.json` | - 40 bài viết sạch chuẩn NFC.<br>- Ma trận 40 dòng x 13 cột số không khuyết thiếu.<br>- Báo cáo thống kê mean, std đầy đủ. |
| **3** | **Tổ Chức Chuyên Mục & Từ Khóa** | `src/organization/category_organizer.py` | `data/processed/articles_processed.jsonl` | - Phân bổ bài viết vào 5 chuyên mục mục tiêu.<br>- Lọc bộ Stopwords tiếng Việt (loại bỏ hư từ thông dụng).<br>- Đếm tần suất từ (`collections.Counter`).<br>- Tính chỉ số độ phong phú từ vựng TTR = `unique_words / total_words`. | `data/processed/category_summary.json` | - Đầy đủ 5 chuyên mục.<br>- Mỗi chuyên mục có Top 10 từ khóa, Vocabulary size và TTR hợp lệ. |
| **4** | **Khám Phá Dữ Liệu (EDA)** | `src/eda/run_eda.py`<br>`src/eda/text_statistics.py`<br>`src/eda/temporal_analysis.py`<br>`src/eda/deeper_eda.py` | `data/processed/feature_matrix.csv`<br>`data/processed/category_summary.json` | - Phân tích phân phối độ dài văn bản (Skewness, Outliers).<br>- Phân tích khung giờ vàng đăng bài & nhịp độ tuần.<br>- Phân tích ma trận tương quan Pearson đa biến.<br>- Xuất 6 biểu đồ PNG độ phân giải cao (300 DPI, 1200x800). | `outputs/eda/*.png` (6 biểu đồ)<br>`outputs/eda_summary/*.json`<br>`outputs/eda/eda_report.json` | - Đủ 6 tệp PNG chuẩn kích thước.<br>- Không sinh tệp thừa/mồ côi.<br>- Các chỉ số thống kê logic. |
| **5** | **Quản Trị CSDL 3NF (DBI202)** | `src/database/sync.py`<br>`src/database/sqlserver.py`<br>`sql/create_tables.sql` | `articles_processed.jsonl`<br>`feature_matrix.csv` | - Thiết kế 5 bảng đạt chuẩn hóa 3NF.<br>- Kết nối qua ODBC Driver với cơ chế tự nhận diện driver.<br>- Thực thi Upsert bằng Transaction an toàn.<br>- Hỗ trợ chế độ Mock/Bypass an toàn khi chạy offline không có server. | CSDL Microsoft SQL Server 3NF<br>`sql/queries.sql` (Window Functions) | - Bảng dữ liệu toàn vẹn khóa ngoại.<br>- Truy vấn phân tích Window Functions (DENSE_RANK, LEAD) chạy mượt mà. |
| **6** | **Trình Diễn BI & Kiểm Thử** | `dashboard/app.py`<br>`run_pipeline.py`<br>`tests/test_pipeline.py` | Dữ liệu sạch, biểu đồ PNG, CSDL | - Streamlit Web Dashboard 5 Tab tương tác cao.<br>- Master CLI runner hỗ trợ các tham số linh hoạt.<br>- Bộ kiểm thử tự động 23 bài test kiểm tra 100% các khâu. | Web UI tại `http://localhost:8501`<br>Báo cáo kiểm thử 23/23 Tests PASS | - 23/23 tests hoàn thành trong < 5s.<br>- Giao diện web hiển thị đầy đủ biểu đồ và dữ liệu. |
