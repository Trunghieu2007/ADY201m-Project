# ADY201m Project

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/database-SQL%20Server%203NF-red.svg)](src/database/schema.sql)
[![Dashboard](https://img.shields.io/badge/dashboard-Streamlit%201.64.0-FF4B4B.svg)](dashboard/app.py)

---

## 1. Giới thiệu Đồ án & Mục tiêu Nghiên cứu

Dự án **ADY201m — Vietnamese News Analytics & Trend Discovery Platform** tập trung hoàn toàn vào phương pháp **Phân tích Mô tả Dữ liệu (Descriptive Data Analysis)** và **Khám phá Xu hướng (Trend Discovery)** theo đúng giáo trình môn học:
- **Loại bỏ hoàn toàn Machine Learning / Mô hình Dự đoán:** Không sử dụng các mô hình phân loại phức tạp, không cần huấn luyện thuật toán hộp đen.
- **Loại bỏ NLP phức tạp:** Sử dụng các kỹ thuật thống kê tần suất từ vựng, độ phong phú ngôn ngữ và bộ lọc từ dừng (Vietnamese Stopwords) trực quan, minh bạch.
- **Tập trung vào Storytelling & Insight:** Chuyển đổi dữ liệu báo chí thô thành các báo cáo và biểu đồ xu hướng sinh động, dễ hiểu cho người dùng.

### 4 Khía cạnh Khám phá Xu hướng Trọng tâm:
1. **Xu hướng Thời gian Xuất bản (Temporal Trends):**
   - *Khung giờ vàng xuất bản:* Nhận diện các khung giờ cao điểm mà tòa soạn VnExpress phát hành tin tức nhiều nhất trong ngày.
   - *Nhịp độ phát hành theo ngày:* So sánh khối lượng tin bài giữa các ngày trong tuần (Weekday) và ngày cuối tuần (Weekend).
   - *Độ trễ thu thập (`publication_to_crawl_gap_minutes`):* Khoảng thời gian từ lúc tin bài được duyệt đăng đến khi hệ thống tiếp cận.
2. **Xu hướng Từ khóa & Chủ đề (Keyword & Topic Trends):**
   - Trích xuất top từ khóa nóng nhất (Trending keywords) trong 5 chuyên mục mục tiêu sau khi loại bỏ stopwords.
   - Phản ánh những mối quan tâm thời sự cốt lõi của xã hội trong từng lĩnh vực.
3. **Xu hướng Định dạng & Dung lượng Nội dung (Content Length Trends):**
   - Phân tích sự phân hóa về độ dài (số từ, số câu, số ký tự) giữa các chuyên mục (chuyên mục nào viết sâu, chuyên mục nào tin vắn).
   - Đánh giá độ phong phú từ vựng (`lexical_diversity`) giữa các nhóm đề tài.
4. **Xu hướng Cơ cấu Chuyên mục (Taxonomy Trends):**
   - Phân tích tỷ trọng và cơ cấu các tiểu mục (`subcategory`) bên trong từng chuyên mục chính.

### 5 Chuyên mục Tin tức Mục tiêu:
1. **Thời sự** (`thoi-su`)
2. **Kinh doanh** (`kinh-doanh`)
3. **Bất động sản** (`bat-dong-san`)
4. **Khoa học công nghệ** (`khoa-hoc-cong-nghe`)
5. **Sức khỏe** (`suc-khoe`)

---

## 2. Thành viên Thực hiện & Phân công Đề tài

| STT | Mã Sinh viên | Vai trò Cốt lõi | Phân công Nhiệm vụ Chi tiết |
| :---: | :---: | :--- | :--- |
| 1 | **HE210442** | **Cào dữ liệu & Làm sạch dữ liệu** | - Xây dựng bộ cào tự động VnExpress qua RSS & Sitemap XML ([`src/crawler/`](src/crawler/)).<br>- Kiểm định chất lượng dữ liệu thô và quản trị mã băm SHA-256 ([`src/validation/validate_raw.py`](src/validation/validate_raw.py)).<br>- Tiền xử lý, chuẩn hóa Unicode NFC và trích xuất 13 đặc trưng mô tả ([`src/preprocessing/preprocess.py`](src/preprocessing/preprocess.py)). |
| 2 | **HE210543** | **Quản lý Database** | - Thiết kế kiến trúc lược đồ CSDL quan hệ chuẩn hóa 3NF ([`src/database/schema.sql`](src/database/schema.sql)).<br>- Xây dựng pipeline nạp đồng bộ (ETL/Upsert) an toàn, chống SQL Injection ([`src/database/sync.py`](src/database/sync.py)).<br>- Quản trị kết nối ODBC, tối ưu hóa chỉ mục và viết truy vấn phân tích nâng cao với Window Functions ([`sql/queries.sql`](sql/queries.sql)). |
| 3 | **HE210370** | **Vẽ sơ đồ trực quan & Dashboard** | - Phân tích khám phá dữ liệu (EDA), phân tích xu hướng thời gian & từ vựng ([`src/eda/`](src/eda/)).<br>- Thiết kế và kết xuất 6 biểu đồ trực quan hóa dữ liệu tĩnh ([`outputs/eda/`](outputs/eda/)).<br>- Phát triển giao diện web BI Dashboard Streamlit 5 Tab tương tác ([`dashboard/app.py`](dashboard/app.py)). |

---

## 3. Luồng Chạy Dữ Liệu (Data Pipeline Flow)

Toàn bộ quy trình xử lý dữ liệu từ lúc cào tin tức từ VnExpress đến khi hiển thị trên giao diện Dashboard được thiết kế theo luồng tuần tự, khép kín và bảo toàn nguyên vẹn 100% dữ liệu gốc:

```mermaid
flowchart LR
    A["🌐 VnExpress\n(Web Articles)"] -->|1. Crawler| B[("data/raw/\narticles.jsonl")]
    B -->|2. EDA| C["outputs/eda/\n(6 Biểu đồ PNG + Report)"]
    B -->|3. Preprocessing| D[("data/processed/\narticles_processed.jsonl\nfeature_matrix.csv")]
    D -->|4. Organization| E[("data/processed/\ncategory_summary.json")]
    D & E -->|5. SQL Sync| F[("MS SQL Server\n(Schema 3NF)")]
    D & E & F -->|6. Render| G["Streamlit Dashboard\n(5 Tabs BI UI)"]
```

### Bảng tóm tắt các chặng luân chuyển dữ liệu:

| Chặng | Tên giai đoạn | Dữ liệu Đầu vào (Input) | Module xử lý chính | Dữ liệu Đầu ra (Output) | Vai trò trong hệ thống |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | **Thu thập (Ingestion)** | RSS Feeds & Sitemap VnExpress | [`src/crawler/`](src/crawler/) | `data/raw/articles.jsonl` | Bóc tách 12 trường cấu trúc dữ liệu thô|
| **2** | **Khám phá (EDA)** | `data/raw/articles.jsonl` | [`src/eda/`](src/eda/) | `outputs/eda/*.png`<br>`outputs/eda_summary/` | Đánh giá phân phối, khung giờ vàng, xuất 6 biểu đồ PNG tĩnh và báo cáo. |
| **3** | **Tiền xử lý (Cleaning)** | `data/raw/articles.jsonl` | [`src/preprocessing/`](src/preprocessing/) | `data/processed/articles_processed.jsonl`<br>`data/processed/feature_matrix.csv` | Chuẩn hóa Unicode NFC, khử tiêu đề lặp, trích xuất 13 đặc trưng mô tả. |
| **4** | **Tổ chức (Taxonomy)** | `articles_processed.jsonl` | [`src/organization/`](src/organization/) | `data/processed/category_summary.json` | Lọc stopwords tiếng Việt, gom nhóm chuyên mục, trích xuất top từ khóa nóng. |
| **5** | **Lưu trữ CSDL (Storage)** | Dữ liệu sạch `data/processed/` | [`src/database/`](src/database/) | CSDL Microsoft SQL Server (3NF) | Tạo 5 bảng chuẩn 3NF, đồng bộ Transaction an toàn, truy vấn Window Functions. |
| **6** | **Trực quan hóa (BI UI)** | Dữ liệu sạch / CSDL SQL Server | [`dashboard/`](dashboard/) | Web App: `http://localhost:8501` | Trình diễn 5 Tab tương tác: KPI, Khám phá Xu hướng, Quản lý tin, CSDL, Kiểm toán. |

---

## 4. Đặc tả Chi tiết Dữ liệu Đầu vào & Đầu ra (Project Input & Output)

Phần này đặc tả tường minh quy cách dữ liệu đầu vào (Input) từ báo điện tử VnExpress và toàn bộ các dạng dữ liệu, biểu đồ, CSDL và giao diện đầu ra (Output) được tạo ra trong toàn bộ dự án.

### 4.1. Dữ liệu Đầu vào của Dự án (Project Inputs)

Hệ thống tiếp nhận 2 tầng dữ liệu đầu vào chính:

#### 1. Nguồn Dữ liệu Bên ngoài (External Data Ingestion)
- **Nguồn cấp tin tức trực tuyến:** Báo điện tử **VnExpress** (`https://vnexpress.net`), trang tin tức có lượng người đọc và uy tín hàng đầu tại Việt Nam.
- **5 Chuyên mục mục tiêu & Giao thức thu thập:**
  - **Thời sự:** RSS Feed `https://vnexpress.net/rss/thoi-su.rss` & Sitemap XML.
  - **Kinh doanh:** RSS Feed `https://vnexpress.net/rss/kinh-doanh.rss` & Sitemap XML.
  - **Bất động sản:** RSS Feed `https://vnexpress.net/rss/bat-dong-san.rss` & Sitemap XML.
  - **Khoa học công nghệ:** RSS Feed `https://vnexpress.net/rss/khoa-hoc.rss` & Sitemap XML.
  - **Sức khỏe:** RSS Feed `https://vnexpress.net/rss/suc-khoe.rss` & Sitemap XML.
- **Tệp cấu hình & Dữ liệu tham chiếu đầu vào:**
  - Tệp cấu hình môi trường `.env`: Khai báo thông số kết nối CSDL Microsoft SQL Server (`ODBC Driver 18/17/13`, Host, Port, Database, User, Password).
  - Bộ lọc Stopwords tiếng Việt: Tích hợp sẵn trong [`src/organization/category_organizer.py`](src/organization/category_organizer.py) chứa danh sách các hư từ tiếng Việt thông dụng (được, có, những, các, và, của, cho, ...) để làm sạch khi trích xuất từ khóa.

#### 2. Dữ liệu Thô Thu thập được (Raw Ingestion Dataset - `data/raw/articles.jsonl`)
- **Quy cách lưu trữ:** Định dạng JSON Lines (`.jsonl`), mỗi dòng là 1 đối tượng JSON đại diện cho 1 bài viết hoàn chỉnh.
- **Quy mô tập mẫu:** 20 bài báo phân bổ cân bằng chính xác trên 5 chuyên mục mục tiêu (4 bài / chuyên mục).
- **Tính bất biến (Data Immutability):** Tệp thô được đóng băng toàn vẹn qua mã băm SHA-256 đối soát tự động bởi [`outputs/dataset_manifest.json`](outputs/dataset_manifest.json), đảm bảo không bị biến đổi trong suốt các pha xử lý.
- **Đặc tả 12 trường cấu trúc của bản ghi thô:**

| STT | Tên trường | Kiểu dữ liệu | Ràng buộc | Ý nghĩa & Mô tả chi tiết |
| :---: | :--- | :---: | :---: | :--- |
| 1 | `url` | `string` | Bắt buộc, Unique | Đường dẫn URL chính thức của bài báo trên VnExpress. |
| 2 | `title` | `string` | Bắt buộc | Tiêu đề chính của bài viết đã lọc bỏ khoảng trắng thừa. |
| 3 | `description` | `string` | Bắt buộc | Đoạn mô tả tóm tắt (Sapo) mở đầu bài báo. |
| 4 | `content` | `string` | Bắt buộc | Toàn bộ nội dung thân bài (bóc tách từ HTML sạch sẽ, loại bỏ triệt để quảng cáo, điều hướng UI, tiêu đề lặp). |
| 5 | `author` | `string` | Nullable | Tên tác giả hoặc ký danh phóng viên (trích xuất từ chữ ký cuối bài, vd: `Hà An`, `Ngọc Điệp`). |
| 6 | `publisher` | `string` | Bắt buộc | Đơn vị xuất bản báo chí (`"VnExpress"`). |
| 7 | `published_at` | `string` | Bắt buộc | Thời điểm đăng bài theo chuẩn ISO 8601 có múi giờ (vd: `2026-03-29T10:15:00+07:00`). |
| 8 | `category` | `string` | Bắt buộc | Tên chuyên mục chính (`Thời sự`, `Kinh doanh`, `Bất động sản`, `Khoa học công nghệ`, `Sức khỏe`). |
| 9 | `subcategory` | `string` | Nullable | Tên tiểu mục chi tiết bóc tách từ Breadcrumbs hoặc URL (vd: `Chính trị`, `Doanh nghiệp`, `Thị trường`). |
| 10 | `article_id` | `string` | Nullable | Mã định danh số tự nhiên của bài báo được bóc tách từ URL VnExpress (vd: `4728192`). |
| 11 | `crawled_at` | `string` | Bắt buộc | Thời điểm hệ thống tiến hành cào dữ liệu theo chuẩn ISO 8601. |
| 12 | `source` | `string` | Bắt buộc | Phương thức phát hiện URL bài viết (`"rss"` hoặc `"sitemap"`). |

- **Nhật ký cào (`data/raw/crawl_log.jsonl`):** Lưu trữ toàn bộ lịch sử các lần cào, thời gian thực hiện, trạng thái HTTP status code và số lượng bài thu thập.

---

### 4.2. Dữ liệu Đầu ra của Dự án (Project Outputs)

Toàn bộ sản phẩm đầu ra của hệ thống được tổ chức thành 5 nhóm thành phẩm rõ ràng:

#### 1. Dữ liệu Tiền xử lý & Ma trận Đặc trưng Thống kê (`data/processed/`)
- [`data/processed/articles_processed.jsonl`](data/processed/articles_processed.jsonl):
  - **Bảo toàn 100% dữ liệu gốc:** Giữ nguyên 12 trường thô ban đầu ở tầng ngoài (Non-destructive).
  - **Trường làm sạch phái sinh:**
    - `processed_text`: Văn bản nội dung được chuẩn hóa bảng mã **Unicode NFC**, loại bỏ URL rác, chuẩn hóa khoảng trắng và giữ nguyên cấu trúc ngữ nghĩa tiếng Việt.
    - `processed_metadata`: Chứa `author_clean` (tên tác giả đã chuẩn hóa, khử dấu đóng ngoặc đơn và ký tự nhiễu).
  - **Đối tượng đặc trưng `features`:** Chứa đúng **13 đặc trưng thống kê mô tả** (không dùng cho Machine Learning):
    - *Độ dài & quy mô:* `char_count` (số ký tự), `word_count` (số từ), `sentence_count` (số câu), `unique_words` (số từ độc nhất).
    - *Phong phú từ vựng:* `lexical_diversity` (tỷ lệ từ độc nhất / tổng số từ), `avg_word_length` (độ dài trung bình ký tự/từ).
    - *Cấu trúc tiêu đề/mô tả:* `title_word_count`, `desc_word_count`, `title_to_content_word_ratio`, `desc_to_content_word_ratio`, `has_author` (cờ nhị phân 0 hoặc 1).
    - *Thời gian xuất bản:* `published_hour` (khung giờ đăng 0–23), `published_dayofweek` (thứ trong tuần 0–6).
- [`data/processed/feature_matrix.csv`](data/processed/feature_matrix.csv): Bảng ma trận 13 đặc trưng dạng số cho toàn bộ 20 bài viết, sẵn sàng mở bằng Excel hoặc nạp trực tiếp vào CSDL.
- [`data/processed/category_summary.json`](data/processed/category_summary.json): Tệp tổng hợp xu hướng theo chuyên mục:
  - Tỷ lệ phần trăm và số lượng bài viết của từng chuyên mục.
  - Số từ trung bình của nội dung bài viết theo từng chuyên mục.
  - Danh sách các tiểu mục xuất hiện trong chuyên mục.
  - **Top từ khóa nóng (Trending Keywords):** Bảng xếp hạng các từ khóa có tần suất xuất hiện cao nhất trong từng chuyên mục kèm số lần xuất hiện (đã lọc stopwords tiếng Việt).

#### 2. Bộ Trực quan hóa Khám phá Dữ liệu Tĩnh (`outputs/eda/`)
Hệ thống tự động xuất 6 biểu đồ phân tích trực quan chất lượng cao (300 DPI) phục vụ nghiên cứu và báo cáo:
- `category_distribution.png`: Phân bổ số lượng và tỷ lệ bài viết trên 5 chuyên mục mục tiêu.
- `category_subcategory.png`: Cơ cấu các tiểu mục trong từng chuyên mục chính.
- `content_length_distribution.png`: Phân phối độ dài nội dung (số từ, số ký tự) bài báo.
- `average_words_by_category.png`: So sánh dung lượng bài viết trung bình giữa các chuyên mục.
- `publication_hour.png`: Khám phá "khung giờ vàng" xuất bản tin tức của tòa soạn trong ngày.
- `publication_to_crawl_gap_by_category.png`: Phân tích độ trễ thu thập tin bài theo từng chuyên mục.
- **Báo cáo tóm tắt:** Tệp Markdown [`outputs/eda_summary/phase2_summary.md`](outputs/eda_summary/phase2_summary.md) phân tích sâu các insight rút ra từ biểu đồ cùng tệp checklist kiểm định [`outputs/eda_summary/phase2_checklist.json`](outputs/eda_summary/phase2_checklist.json).

#### 3. Cơ sở Dữ liệu Quan hệ Microsoft SQL Server Chuẩn 3NF
Dữ liệu sạch được nạp vào Microsoft SQL Server thông qua cơ chế Transaction an toàn:
- **5 Bảng quan hệ chuẩn hóa 3NF:**
  - `dbo.Categories`: Bảng danh mục gốc (`category_id` [PK], `name` [UQ]).
  - `dbo.Subcategories`: Bảng tiểu mục (`subcategory_id` [PK], `category_id` [FK], `name`).
  - `dbo.Authors`: Bảng tác giả (`author_id` [PK], `name` [UQ]).
  - `dbo.Articles`: Bảng sự kiện bài viết chính (`article_id` [PK], `url` [UQ], các FK trỏ về chuyên mục, tiểu mục, tác giả).
  - `dbo.ArticleFeatures`: Bảng quan hệ 1:1 mở rộng lưu trữ 13 đặc trưng mô tả (`article_id` [PK, FK]).
- **Sơ đồ ERD:** Tệp đồ họa trực quan [`outputs/database/erd_diagram.png`](outputs/database/erd_diagram.png) độ phân giải cao 300 DPI.
- **Biên bản nạp:** Tệp [`outputs/database/import_manifest.json`](outputs/database/import_manifest.json) ghi nhận chi tiết số bản ghi import, update và tỷ lệ toàn vẹn khóa ngoại.

#### 4. Ứng dụng BI Dashboard Tương tác (Streamlit Web UI)
Giao diện trực quan hóa thông minh phục vụ người dùng cuối tại `http://localhost:8501` gồm 5 Tab:
- **Tab 1 — Tổng quan (Overview):** KPI thẻ điểm (Total Articles, Categories, Words, Authors), phân bố chuyên mục và trình duyệt tin bài.
- **Tab 2 — Khám phá Xu hướng (Trend Discovery):** Tương tác với xu hướng khung giờ đăng bài, ngày trong tuần, độ dài nội dung và đám mây từ khóa theo chuyên mục.
- **Tab 3 — Quản lý Chuyên mục (Taxonomy):** Thống kê phân cấp chuyên mục - tiểu mục và tỷ trọng đóng góp nội dung.
- **Tab 4 — CSDL SQL Server 3NF:** Tra cứu trạng thái kết nối CSDL, xem cấu trúc bảng và thực thi các truy vấn nâng cao (Window Functions, CTE).
- **Tab 5 — Kiểm toán & Toàn vẹn (Audit):** Đối soát mã băm SHA-256 dữ liệu thô, kiểm tra tính bất biến của dữ liệu.

#### 5. Báo cáo Kiểm toán Toàn diện Chất lượng Dữ liệu (`outputs/`)
- [`outputs/dataset_manifest.json`](outputs/dataset_manifest.json): Biên bản đóng băng mã băm SHA-256 xác thực nguồn dữ liệu gốc.
- [`outputs/project_audit.json`](outputs/project_audit.json): Báo cáo tự động kiểm tra 40 tiêu chí kỹ thuật: không rò rỉ giao diện web (UI noise), không trùng lặp khối văn bản, tính bất biến dữ liệu thô (Trạng thái: `PASS_WITH_REVIEW`).

---

## 5. Cấu trúc Thư mục Dự án

```text
ADY201m Project/
├── dashboard/                            # Ứng dụng BI Dashboard Streamlit
│   ├── app.py                            # Streamlit BI Dashboard trực quan hóa xu hướng
│   └── run_dashboard.py                  # Entrypoint khởi chạy nhanh Streamlit
├── data/
│   ├── processed/                        # Dữ liệu sạch sau tiền xử lý
│   │   ├── articles_processed.jsonl      # Dữ liệu JSONL kèm trường phái sinh & 13 đặc trưng
│   │   ├── category_summary.json         # Tóm tắt tổ chức chuyên mục & top từ khóa xu hướng
│   │   └── feature_matrix.csv            # Ma trận 13 đặc trưng thống kê mô tả
│   └── raw/                              # Dữ liệu cào gốc (Đóng băng)
│       ├── articles.jsonl                # 20 bản ghi gốc
│       └── crawl_log.jsonl               # Nhật ký thu thập dữ liệu
├── outputs/                              # Toàn bộ dữ liệu xuất, báo cáo, manifest, biểu đồ
│   ├── database/                         # Manifest tích hợp CSDL SQL Server & Sơ đồ ERD (erd_diagram.png)
│   ├── eda/                              # 6 biểu đồ phân tích EDA (.png) & JSON kết quả
│   ├── eda_summary/                      # Tóm tắt & checklist EDA (Markdown & JSON)
│   ├── preprocessing/                    # Manifest tiền xử lý & Feature summary
│   ├── dataset_manifest.json             # Manifest SHA-256 dữ liệu thô
│   └── project_audit.json                # Báo cáo kiểm toán chất lượng toàn diện
├── sql/                                  # Kịch bản DDL/DML Microsoft SQL Server
│   ├── create_database.sql               # Tạo CSDL ADY201m
│   ├── create_tables.sql                 # Tạo 5 bảng chuẩn 3NF & chỉ mục
│   ├── upsert_article.sql                # Hợp đồng tham số hóa UPDATE/INSERT
│   └── queries.sql                       # 6 truy vấn phân tích nghiệp vụ & Window Functions
├── src/                                  # Mã nguồn chính của dự án
│   ├── crawler/                          # Bóc tách RSS, Sitemap, Bài báo VnExpress & validate
│   ├── database/                         # Kết nối pyodbc & nạp SQL Server 3NF (run_database.py), vẽ ERD (draw_erd.py)
│   ├── eda/                              # Thống kê văn bản & xu hướng thời gian (run_eda.py)
│   ├── organization/                     # Tự động tổ chức chuyên mục & xu hướng từ khóa (category_organizer.py)
│   ├── preprocessing/                    # Chuẩn hóa Unicode NFC & trích xuất đặc trưng (preprocess.py)
│   └── validation/                       # Kiểm tra chất lượng dữ liệu & Audit toàn dự án
├── tests/
│   └── test_pipeline.py                  # Bộ kiểm thử hồi quy tự động (unittest)
├── .env.example                          # Mẫu biến môi trường kết nối SQL Server
├── .gitignore                            # Cấu hình bỏ qua file nhị phân & môi trường ảo
├── Knowledge.md                          # Cơ sở tri thức chuẩn môn học ADY201m
├── requirements.txt                      # Thư viện pipeline chính (Data + SQL)
├── requirements-streamlit.txt            # Thư viện cho Dashboard Streamlit
└── README.md                             # Tài liệu hướng dẫn dự án
```

---

## 6. Chi tiết Các Giai đoạn Thực hiện (Phases 1 — 6)

### Phase 1: Thu thập Dữ liệu & Kiểm định Chất lượng
- **Bộ cào tự động:** [`src/crawler/`](src/crawler/) sử dụng RSS và Sitemap XML để phát hiện bài viết mới và bóc tách HTML chi tiết với `BeautifulSoup(..., 'lxml')`.
- **Cơ chế thu thập:** Lấy mẫu cân bằng chính xác 20 bài (4 bài x 5 chuyên mục mục tiêu).
- **Bộ lọc thông minh:**
  - Ngăn chặn triệt để việc rò rỉ tiêu đề và mô tả lặp lại ở đầu bài viết.
  - Tách tác giả dựa trên cấu trúc thẻ căn phải (`align="right"` trước `#article-end`), loại bỏ thông tin hậu kỳ (`Nhóm thiết kế:`, `Kết cấu:`, `Ảnh:`).
  - Cơ chế retry 3 lần với exponential backoff cho lỗi mạng tạm thời.
- **Kiểm định dữ liệu:** [`src/crawler/validate_raw.py`](src/crawler/validate_raw.py) và [`src/validation/create_manifest.py`](src/validation/create_manifest.py) xác thực 12 trường cấu trúc, đảm bảo không có bản ghi lỗi hay trùng lặp.

### Phase 2: Phân tích Dữ liệu Khám phá (EDA) & Xu hướng Cơ bản
- **Thống kê từ vựng:** Tính toán số ký tự, số từ, số câu, số từ độc nhất và độ dài trung bình của từ cho nội dung, tiêu đề và mô tả.
- **Phân tích xu hướng thời gian:** Tính toán chênh lệch thời gian từ lúc bài viết xuất bản đến lúc crawler thu thập (`publication_to_crawl_gap_minutes`).
- **Trực quan hóa:** Tự động xuất 6 biểu đồ đồ họa sắc nét vào thư mục [`outputs/eda/`](outputs/eda/):
  - `average_words_by_category.png` (Số từ trung bình theo chuyên mục)
  - `category_distribution.png` (Phân bố chuyên mục)
  - `category_subcategory.png` (Phân bố tiểu mục)
  - `content_length_distribution.png` (Phân phối độ dài nội dung)
  - `publication_hour.png` (Phân phối giờ xuất bản)
  - `publication_to_crawl_gap_by_category.png` (Độ trễ thu thập theo chuyên mục)

### Phase 3: Tiền xử lý Dữ liệu & Chuẩn hóa Unicode NFC
- **Chuẩn hóa văn bản:** Chuẩn hóa Unicode NFC (tránh lỗi font tiếng Việt tổ hợp), loại bỏ khoảng trắng thừa, xóa URL khỏi văn bản phái sinh mà không làm ảnh hưởng nội dung gốc.
- **Chuẩn hóa tác giả:** Tách riêng `author_clean` (ví dụ gộp `( Tổng hợp )` thành `tổng hợp`), bảo toàn nguyên trạng trường `author` thô.
- **Sinh đặc trưng mô tả:**
  - 13 đặc trưng số văn bản: số ký tự, số từ, số câu, từ độc nhất, độ đa dạng từ vựng (`lexical_diversity`), độ dài từ trung bình, đặc trưng tiêu đề/mô tả, tỷ lệ từ tiêu đề/nội dung, giờ đăng và thứ trong tuần.
  - Ma trận `feature_matrix.csv` lưu trữ sẵn sàng cho tích hợp CSDL và trực quan hóa.

### Phase 4: Khám phá Xu hướng Từ khóa & Tự động Tổ chức Chuyên mục
- **Bóc tách danh mục tự nhiên (Natural Taxonomy Extraction):**
  - Chuyên mục (`category`) và tiểu mục (`subcategory`) được bóc tách trực tiếp từ cấu trúc URL đường dẫn của VnExpress (`https://vnexpress.net/<category>/...`) kết hợp thẻ breadcrumbs.
  - Ánh xạ về 5 chuyên mục chuẩn hóa qua module [`src/organization/category_organizer.py`](src/organization/category_organizer.py).
- **Phát hiện từ khóa xu hướng không cần mô hình phức tạp:**
  - Lọc bỏ danh sách stopwords tiếng Việt phổ biến.
  - Thống kê tần suất từ vựng để tìm ra các chủ đề nóng nhất trong từng chuyên mục.
  - Xuất file tổng hợp thông minh `data/processed/category_summary.json`.

### Phase 5: Tích hợp CSDL Microsoft SQL Server Chuẩn 3NF
- **Lược đồ quan hệ chuẩn hóa 3NF:**
  - `dbo.Categories`: Bảng danh mục gốc (`category_id` [PK], `name` [UQ]).
  - `dbo.Subcategories`: Bảng tiểu mục (`subcategory_id` [PK], `category_id` [FK trỏ về Categories], `name`).
  - `dbo.Authors`: Bảng tác giả (`author_id` [PK], `name` [UQ]).
  - `dbo.Articles`: Bảng lưu trữ bài viết với khóa chính tự nhiên `article_id` [PK], URL duy nhất `url` [UQ], và các khóa ngoại `author_id` [FK], `category_id` [FK], `subcategory_id` [FK].
  - `dbo.ArticleFeatures`: Bảng mở rộng 1 : 1 lưu 13 đặc trưng từ vựng và thời gian (`article_id` [PK, FK trỏ về Articles]).

#### Sơ đồ Quan hệ Thực thể (Entity-Relationship Diagram - ERD):
<p align="center">
  <img src="outputs/database/erd_diagram.png" alt="Sơ đồ ERD CSDL Microsoft SQL Server 3NF" width="100%" />
</p>

- **Tính toàn vẹn & Truy vấn Báo cáo Xu hướng:**
  - Sử dụng câu lệnh tham số hóa (Parameterized SQL) chống tấn công SQL Injection.
  - Hỗ trợ các truy vấn phân tích xu hướng với Window Functions (`ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY published_at DESC)`).
  - Cơ chế đồng bộ an toàn: Kiểm tra bài viết đã tồn tại thì thực hiện `UPDATE`, nếu chưa có thì `INSERT` trong cùng Transaction.


### Phase 6: Giao diện BI Dashboard Khám phá Xu hướng (Streamlit)
- Nền tảng Dashboard tương tác gồm 5 tab chức năng:
  1. **Tổng quan (Overview):** Thống kê tổng số bài viết, tỷ lệ phân bố chuyên mục và bảng duyệt toàn bộ tin tức.
  2. **Khám phá Xu hướng & EDA (Trend Discovery):**
     - Biểu đồ khung giờ vàng xuất bản tin tức.
     - Biểu đồ nhịp điệu phát hành theo ngày trong tuần.
     - Biểu đồ top từ khóa thịnh hành theo từng chuyên mục.
     - So sánh dung lượng bài viết trung bình giữa các chuyên mục.
  3. **Quản lý & Tự động Phân loại Tin tức (Auto-Organize):** Trình duyệt tin tức theo chuyên mục, xem bài viết chi tiết và liên kết nguồn VnExpress.
  4. **CSDL SQL Server 3NF:** Khám phá cấu trúc bảng và chạy thử nghiệm trực tiếp các câu truy vấn SQL phân tích nghiệp vụ.
  5. **Kiểm toán & Tính Toàn vẹn (Audit):** Báo cáo kiểm định toàn diện chất lượng dữ liệu, mã băm SHA-256 đóng băng dữ liệu thô.

---

### Danh mục Kỹ thuật Các Module & Hàm Chi tiết

Mỗi hàm trong mã nguồn được chú thích bằng 1 dòng comment `#` súc tích; tài liệu kỹ thuật tập trung được liệt kê tại đây:

#### 1. Module Thu thập Dữ liệu (`src/crawler/`)
- [`src/crawler/crawler.py`](src/crawler/crawler.py):
  - `fetch_url(url: str, retries: int, delay: float) -> str`: Tải trang với cơ chế retry và header giả lập trình duyệt.
  - `ArticleCrawler`: Bóc tách 12 trường cấu trúc bài viết (tiêu đề, mô tả, nội dung, tác giả, thời gian xuất bản, chuyên mục, ID).
  - `RSSCrawler`: Bóc tách và quét danh sách tin bài từ luồng RSS của 5 chuyên mục mục tiêu.
  - `SitemapCrawler`: Bóc tách danh sách URL bài báo từ XML sitemap của VnExpress.
  - `main()`: Điều phối cào cân bằng 5 chuyên mục mục tiêu và lưu vào `data/raw/articles.jsonl`.
- [`src/crawler/article.py`](src/crawler/article.py):
  - `ArticleParser`: Bóc tách chi tiết cấu trúc HTML5 từng bài báo (tiêu đề `h1.title-detail`, mô tả, nội dung `article.fck_detail`, tác giả, thời gian xuất bản).
- [`src/crawler/validate_raw.py`](src/crawler/validate_raw.py):
  - `load_jsonl(path: Path) -> tuple[list[dict], list[str]]`: Tải các dòng dữ liệu JSONL và bắt lỗi cú pháp.
  - `count_empty_fields(records: list[dict]) -> Counter[str]`: Đếm số lượng trường bắt buộc bị rỗng hoặc thiếu.
  - `find_duplicate_urls(records: list[dict]) -> list[str]`: Tìm kiếm các URL bài viết xuất hiện nhiều hơn 1 lần.
  - `schema_issues(records: list[dict]) -> list[dict]`: Kiểm tra tính khớp nối của các trường so với schema mong đợi.
  - `timestamp_issues(records: list[dict], field: str) -> list[dict]`: Kiểm tra định dạng thời gian ISO 8601 hợp lệ.
  - `invalid_urls(records: list[dict]) -> list[dict]`: Xác thực các URL phải thuộc tên miền VnExpress.
  - `calculate_content_statistics(lengths: list[int]) -> dict`: Tính các chỉ số thống kê độ dài nội dung.

#### 2. Module Kiểm định Chất lượng (`src/validation/`)
- [`src/validation/create_manifest.py`](src/validation/create_manifest.py):
  - `calculate_sha256(path: Path) -> str`: Tính toán mã băm SHA-256 của toàn bộ tệp dữ liệu thô.
  - `load_records(path: Path) -> list[dict]`: Đọc danh sách bản ghi JSONL mà không thay đổi tệp gốc.
  - `inspect_schema(records: list[dict]) -> dict`: Xác thực cấu trúc schema chuẩn trên từng bản ghi.
  - `generate_manifest() -> dict`: Tạo tệp `outputs/dataset_manifest.json` ghi nhận thông tin kiểm định.
- [`src/validation/project_audit.py`](src/validation/project_audit.py):
  - `audit_content_quality(records, json_errors) -> dict`: Kiểm định chuyên sâu chất lượng bóc tách nội dung, phát hiện rò rỉ giao diện, trùng lặp và lỗi mã hóa.
  - `main() -> dict`: Chạy kiểm toán toàn diện tất cả các giai đoạn trong pipeline và xuất báo cáo `outputs/project_audit.json`.

#### 3. Module Phân tích Dữ liệu Khám phá (`src/eda/`)
- [`src/eda/text_statistics.py`](src/eda/text_statistics.py):
  - `word_count(text: str) -> int`: Đếm số từ theo phân tách khoảng trắng.
  - `sentence_count(text: str) -> int`: Đếm số câu dựa trên dấu chấm, hỏi, cảm thán.
  - `unique_word_count(text: str) -> int`: Đếm số từ độc nhất sau chuẩn hóa.
  - `average_word_length(text: str) -> float`: Tính độ dài ký tự trung bình của từ.
  - `analyze_articles(articles: list[dict]) -> dict`: Tổng hợp chỉ số thống kê từ vựng toàn tập bài viết và lưu vào `outputs/eda/text_statistics.json`.
- [`src/eda/temporal_analysis.py`](src/eda/temporal_analysis.py):
  - `parse_datetime(value: Any) -> datetime | None`: Phân tích chuỗi ISO thời gian.
  - `publication_to_crawl_gap_minutes(published, crawled) -> float | None`: Đo độ lệch phút giữa lúc xuất bản và lúc crawl.
  - `analyze_articles(articles: list[dict]) -> dict`: Tổng hợp phân bố ngày, giờ xuất bản và lưu vào `outputs/eda/temporal_analysis.json`.
- [`src/eda/deeper_eda.py`](src/eda/deeper_eda.py):
  - `analyze_category_relationships(articles: list[dict]) -> dict`: Phân tích ma trận quan hệ giữa category và subcategory.
  - `analyze_text_by_category(articles: list[dict]) -> dict`: Thống kê độ dài từ vựng phân loại theo từng chuyên mục.
  - `save_outputs(report, articles)`: Lưu báo cáo JSON, tóm tắt văn bản và sinh 6 biểu đồ PNG sắc nét vào `outputs/eda/`.
- [`src/eda/run_eda.py`](src/eda/run_eda.py):
  - `validate_eda_outputs() -> dict`: Tự kiểm tra đối soát tính toàn vẹn của 6 biểu đồ trực quan PNG và 7 tệp báo cáo thống kê EDA.
  - `main()`: Điều phối toàn bộ quy trình EDA, xuất checklist kiểm định và tóm tắt markdown `outputs/eda_summary/phase2_summary.md`. Hỗ trợ cờ `--check` để kiểm tra nhanh tính đầy đủ của kết quả mà không cần render lại biểu đồ.

#### 4. Module Tiền xử lý & Làm sạch Dữ liệu (`src/preprocessing/`)
- [`src/preprocessing/preprocess.py`](src/preprocessing/preprocess.py):
  - Hợp nhất toàn diện quy trình làm sạch văn bản, chuẩn hóa tác giả, trích xuất 13 đặc trưng mô tả và tự động kiểm định:
    - `normalize_unicode(text: str) -> str`: Chuẩn hóa văn bản sang bảng mã Unicode NFC.
    - `normalize_text(text: str) -> str`: Loại bỏ URL rác, quy chuẩn khoảng trắng và giữ nguyên dấu câu tiếng Việt.
    - `remove_leading_duplicate_blocks(content, title, description) -> str`: Khử triệt để phần tiêu đề/mô tả lặp lại ở đầu bài viết.
    - `lexical_features(text: str) -> dict`: Tính các đặc trưng thống kê từ vựng xác định.
    - `normalize_author(author: str | None) -> str | None`: Chuẩn hóa tên tác giả sang trường phái sinh `author_clean`, không ghi đè trường `author` thô.
    - `preprocess_record(record, category_map, subcategory_map) -> dict`: Tiền xử lý bài viết, tạo `processed_text`, `processed_metadata` và `features` (13 chỉ số thống kê mô tả cho CSDL).
    - `build_feature_matrix(rows) -> tuple[list[str], list[list]]`: Tạo ma trận 13 đặc trưng thống kê mô tả phục vụ trực tiếp bảng `dbo.ArticleFeatures`.
    - `validate(...) -> dict`: Tự động kiểm tra bảo đảm tính bất biến của dữ liệu gốc và xác nhận tính toàn vẹn của kết quả tiền xử lý (không dùng SHA-256).
    - `run() -> dict`: Điều phối tạo tệp `data/processed/articles_processed.jsonl` và `data/processed/feature_matrix.csv`, lưu manifest vào `outputs/preprocessing/`.
    - `main()`: Hỗ trợ chạy dòng lệnh linh hoạt qua CLI:
      - `python -m src.preprocessing.preprocess`: Chạy toàn bộ biến đổi và tự kiểm định.
      - `python -m src.preprocessing.preprocess --check`: Chỉ kiểm tra tính toàn vẹn dữ liệu đã qua tiền xử lý.

#### 5. Module Tự động Tổ chức Chuyên mục & Xu hướng Từ khóa (`src/organization/`)
- [`src/organization/category_organizer.py`](src/organization/category_organizer.py):
  - `extract_category_from_url(url: str) -> str`: Bóc tách tự nhiên tên chuyên mục chuẩn hóa từ slug URL VnExpress.
  - `organize_articles(records: list[dict]) -> dict`: Phân nhóm bài viết theo chuyên mục tương ứng.
  - `get_top_keywords(records: list[dict], top_n: int) -> list[tuple]`: Trích xuất top từ khóa xu hướng sau khi lọc bỏ stopwords tiếng Việt.
  - `compute_category_summary(records: list[dict]) -> dict`: Tính toán tỷ lệ phần trăm bài viết, số từ trung bình, tiểu mục và từ khóa đại diện.
  - `validate_summary() -> dict`: Tự động kiểm tra tính hợp lệ của tệp tổng hợp trên đĩa.
  - `main()`: Lưu cấu trúc chuyên mục vào `data/processed/category_summary.json` và hỗ trợ cờ `--check` tự kiểm định nhanh.

#### 6. Module Cơ sở Dữ liệu Microsoft SQL Server (`src/database/`)
- [`src/database/sqlserver.py`](src/database/sqlserver.py):
  - `build_connection_string() -> str`: Tự động nhận diện ODBC Driver (`ODBC Driver 18/17/13`, `SQL Server`) và instance cục bộ (`localhost\SQLEXPRESS`, `localhost`).
  - `get_connection()`: Mở kết nối `pyodbc` an toàn, tích hợp converter xử lý chuẩn kiểu dữ liệu `DATETIMEOFFSET` (-155) sang chuỗi ISO 8601.
  - `split_sql_batches(sql_text: str) -> list[str]`: Tách các khối lệnh SQL theo từ khóa batch `GO`.
  - `execute_schema(cursor) -> int`: Thi hành script DDL tạo 5 bảng chuẩn 3NF và chỉ mục tối ưu hóa.
  - `ensure_dimension(cursor, table, name, category_id)`: Trả về khóa ID hoặc tự động thêm mới bản ghi bảng chiều (`Categories`, `Subcategories`, `Authors`).
  - `import_record(cursor, record) -> bool`: Chèn bản ghi bài viết mới kèm 13 đặc trưng mô tả cho bảng `dbo.ArticleFeatures`.
  - `update_record(cursor, record) -> bool`: Cập nhật bản ghi bài viết và đặc trưng đã tồn tại bằng câu truy vấn tham số hóa an toàn (chống SQL Injection).
  - `sync_records(connection, records) -> tuple[int, int]`: Thực hiện đồng bộ hàng loạt trong 1 transaction an toàn (`commit`/`rollback`).
  - `verify_database(connection, records) -> dict`: Tự động đối soát toàn vẹn CSDL (Reconciliation), kiểm tra số lượng bản ghi (20/20), khóa ngoại mồ côi và đặc trưng mô tả.
  - `main()`: CLI hỗ trợ: `--init-schema`, `--import`, `--update`, `--sync`, `--check`.
- [`src/database/run_database.py`](src/database/run_database.py):
  - Entrypoint khởi chạy nhanh, hỗ trợ đầy đủ các cờ CLI `--sync` và `--check`.
- [`src/database/draw_erd.py`](src/database/draw_erd.py):
  - `draw_erd(output_path: Path | None = None) -> Path`: Tự động kết xuất sơ đồ quan hệ thực thể (ERD) trực quan của 5 bảng CSDL chuẩn 3NF sang tệp ảnh PNG chất lượng cao 300 DPI với nhãn quan hệ 1:N và 1:1 rõ ràng.
  - `main()`: Entrypoint dòng lệnh CLI để tái tạo sơ đồ bất cứ lúc nào (`python -m src.database.draw_erd`).

#### 7. Giao diện BI Dashboard Streamlit (`dashboard/`)
- [`dashboard/app.py`](dashboard/app.py):
  - Ứng dụng Streamlit hiển thị 5 tab tương tác: Tổng quan, Khám phá Xu hướng & EDA, Quản lý & Phân loại Chuyên mục, CSDL SQL Server 3NF, Kiểm toán Tính toàn vẹn.
- [`dashboard/run_dashboard.py`](dashboard/run_dashboard.py):
  - Script khởi chạy nhanh tiện lợi: `python -m dashboard.run_dashboard`.

---

## 7. Hướng dẫn Cài đặt & Khởi chạy Nhanh (Setup Guide cho Người Mới)

Phần này hướng dẫn chi tiết từng bước cho người mới bắt đầu thiết lập môi trường và chạy dự án từ đầu đến cuối trên máy tính cá nhân.

### 7.1. Yêu cầu Tiên quyết (Prerequisites)
Trước khi bắt đầu, hãy đảm bảo máy tính đã cài đặt:
1. **Python 3.10 trở lên** (Khuyến nghị 3.11, 3.12, 3.13 hoặc 3.14). Tải tại [python.org](https://www.python.org/downloads/).
   *(Khi cài đặt trên Windows, nhớ tích chọn ô **"Add Python to PATH"**)*.
2. **Git** để quản lý mã nguồn. Tải tại [git-scm.com](https://git-scm.com/).
3. *(Tùy chọn)* **Microsoft SQL Server** (bản Developer hoặc Express) và **ODBC Driver 18 for SQL Server** nếu bạn muốn nạp dữ liệu vào CSDL quan hệ. Nếu chưa có SQL Server, bạn vẫn có thể chạy toàn bộ pipeline và Dashboard bình thường vì hệ thống tự động đọc dữ liệu từ tệp cục bộ.

---

### 7.2. Các Bước Cài đặt Môi trường (Environment Setup)

#### Bước 1: Tải mã nguồn về máy
Mở Terminal (hoặc PowerShell trên Windows) và chạy lệnh:
```bash
git clone https://github.com/Trunghieu2007/ADY201m-Project.git
cd ADY201m-Project
```

#### Bước 2: Khởi tạo và Kích hoạt Môi trường ảo (Virtual Environment)
Tạo môi trường ảo `.venv` độc lập để tránh xung đột thư viện:
```bash
# Tạo môi trường ảo
python -m venv .venv
```

Kích hoạt môi trường ảo:
- **Trên Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
  > 💡 *Mẹo xử lý lỗi trên Windows PowerShell:* Nếu gặp thông báo lỗi `cannot be loaded because running scripts is disabled on this system`, hãy chạy lệnh sau một lần để cấp quyền:
  > ```powershell
  > Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  > .venv\Scripts\Activate.ps1
  > ```
- **Trên Windows (Command Prompt - cmd):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Trên macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```
*(Khi kích hoạt thành công, bạn sẽ thấy tiền tố `(.venv)` xuất hiện ở đầu dòng lệnh).*

#### Bước 3: Cài đặt các Thư viện Phụ thuộc (Dependencies)
Nâng cấp `pip` và cài đặt đầy đủ các gói thư viện cần thiết:
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-streamlit.txt
```

---

### 7.3. Hướng dẫn Khởi chạy Dự án

Bạn có 2 cách tiếp cận tùy theo nhu cầu:

#### Cách 1: Xem ngay Giao diện Dashboard (Khởi chạy Nhanh)
Dự án đã có sẵn tập dữ liệu mẫu chuẩn hóa trong thư mục `data/`. Bạn có thể mở ngay Dashboard để xem trực quan hóa mà không cần chạy lại pipeline:
```bash
streamlit run dashboard/app.py
```
*(Hoặc dùng lệnh tiện ích: `python -m dashboard.run_dashboard`)*

Trình duyệt web sẽ tự động mở tại địa chỉ: **`http://localhost:8501`**.

---

#### Cách 2: Tự chạy Lại Toàn bộ Quy trình từ A đến Z (End-to-End Pipeline)

Nếu bạn muốn trải nghiệm toàn bộ quy trình từ lúc cào tin tức đến khi hiển thị:

```bash
# 1. Thu thập tin tức mới từ VnExpress (20 bài / 5 chuyên mục)
python -m src.crawler.crawler

# 2. Kiểm định kỹ thuật dữ liệu vừa cào
python -m src.validation.validate_raw

# 3. Phân tích Khám phá Dữ liệu (EDA) & sinh 6 biểu đồ PNG
python -m src.eda.run_eda

# 4. Tiền xử lý, chuẩn hóa Unicode NFC & trích xuất 13 đặc trưng mô tả
python -m src.preprocessing.preprocess

# 5. Tự động nhóm chuyên mục & trích xuất Top từ khóa nóng
python -m src.organization.category_organizer

# 6. (Tùy chọn) Nạp và đồng bộ vào CSDL Microsoft SQL Server 3NF
# Cấu hình biến môi trường kết nối (nếu dùng SQL Server cục bộ):
# $env:ADY_SQLSERVER_SERVER = "localhost"
# $env:ADY_SQLSERVER_DATABASE = "ADY201m"
python -m src.database.run_database --sync

# 7. Khởi chạy Giao diện Streamlit BI Dashboard
streamlit run dashboard/app.py
```

---

### 7.4. Kiểm thử Hệ thống (Verification & Quality Gates)

Để đảm bảo toàn bộ mã nguồn hoạt động chính xác và không có lỗi:
```bash
# Chạy bộ unit tests tự động (23/23 tests PASS)
python -m unittest discover -s tests -v

# Chạy kiểm toán toàn diện tính toàn vẹn dữ liệu và mã băm SHA-256
python -m src.validation.project_audit
```
