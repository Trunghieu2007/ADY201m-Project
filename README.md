# Báo cáo dự án nhóm 6 (Mô tả & Phân loại dữ liệu từ báo VnExpress)

Thành viên nhóm và phân công:

**Đinh Trung Hiếu**: phụ trách phân tích dữ liệu (EDA)

**Phạm Hùng Dương**: phụ trách web crawler

**Nguyễn Hữu Hùng**: phụ trách SQL & Tích hợp mô hình AI

---

## 1. Kiến trúc hệ thống và Cơ sở lý thuyết Data Science

Dự án được xây dựng và chuẩn hóa dựa trên **Phương pháp luận Khoa học Dữ liệu (Data Science Methodology) của John Rollins**, bao gồm vòng đời hoàn chỉnh 9 giai đoạn với các cơ chế lặp (feedback loop) và cổng kiểm định chất lượng:

```
[START: Dự án Data Science / AI]
       │
       ▼
[1. Business Understanding] ──> [2. Analytic Approach] ──> [3. Data Requirements] ──> [4. Data Collection]
                                                                                             │
   ┌─────────────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
[5. Data Understanding / EDA] ◄─── (Dữ liệu chưa đủ tốt?) ───┐
   │                                                         │
   ▼ (Dữ liệu đạt chuẩn)                                     │
[6. Data Preparation] ───────────────────────────────────────┘
   │
   ▼
[7. Modeling]
   │
   ▼
[8. Evaluation] ──(Chưa đạt tiêu chí?)──> Quay lại [1. Business Understanding]
   │
   ▼ (Đạt tiêu chí thành công)
[9. Deployment] ──> [Feedback & Monitoring] ──(Cần cải tiến?)──> Quay lại [1. Business Understanding]
```

### 1.1. Chi tiết 9 giai đoạn theo phương pháp luận John Rollins

#### Giai đoạn 1: Business Understanding (Xác định bài toán & Thấu hiểu nghiệp vụ)

- **Problem Statement (Phát biểu bài toán):** Dữ liệu tin tức báo chí điện tử (VnExpress) xuất bản với số lượng lớn mỗi ngày nhưng rời rạc, chưa có hệ thống tự động theo dõi tần suất, phân bố chủ đề và tự động phân loại chuyên mục cho các bài báo mới.
- **Objectives (Mục tiêu):**
  - Xây dựng hệ thống tự động hóa khép kín (end-to-end pipeline) từ cào dữ liệu, lọc sạch, lưu trữ cơ sở dữ liệu quan hệ đến trực quan hóa thống kê mô tả.
  - Xây dựng mô hình học máy (Machine Learning) có khả năng đọc hiểu nội dung văn bản tiếng Việt và gán nhãn chuyên mục chuẩn xác.
- **Success Criteria (Tiêu chí thành công):**
  - Pipeline vận hành ổn định định kỳ không lỗi, chống trùng lặp dữ liệu tuyệt đối (Primary Key integrity).
  - Khám phá và biểu diễn rõ nét các xu hướng xuất bản qua hệ thống biểu đồ EDA chất lượng cao.
  - Mô hình AI phân loại chuyên mục đạt độ chính xác cao (Accuracy > 70% trên tập dữ liệu đa lớp phức tạp), giải quyết tốt vấn đề Overfitting và rò rỉ dữ liệu (Data Leakage).

#### Giai đoạn 2: Analytic Approach (Xác định hướng tiếp cận phân tích)

- **Phân tích mô tả (Descriptive Analytics):** Sử dụng các kỹ thuật thống kê mô tả và trực quan hóa (EDA) để giải thích *“Điều gì đã và đang diễn ra trên kênh truyền thông?”* (Cơ cấu chuyên mục, khung giờ phát hành cao điểm, cơ cấu tác giả, mật độ xuất bản theo ngày).
- **Phân tích dự đoán & Phân loại (Predictive / Classification Analytics):** Sử dụng học có giám sát (Supervised Learning - Text Classification) để trả lời *“Bài viết này thuộc về chuyên mục nào dựa trên ngữ cảnh tiêu đề và nội dung?”*.
  - *Mô hình chủ đạo:* **Cây quyết định (Decision Tree Classifier)** mang tính diễn giải cao (white-box model), cho phép phân tích rõ các đặc trưng quyết định (Feature Importance).
  - *Mô hình đối chứng:* **Multinomial Naive Bayes** đóng vai trò baseline đối sánh độ chính xác và độ phức tạp tính toán.

#### Giai đoạn 3: Data Requirements (Xác định yêu cầu dữ liệu)

- **Data Schema & Variables:** Bảng dữ liệu báo chí gồm các trường định danh (`article_id`), nội dung văn bản (`title`, `description`, `content`), nguồn gốc (`author`, `url`), thời gian (`published_at`) và nhãn phân loại (`category`, `subcategory`).
- **Sources:** Cổng thông tin điện tử VnExpress qua 16 kênh chuẩn RSS Feeds chính thống.
- **Data Quality Requirements:** Bài báo phải là văn bản gốc hợp lệ (`og:type = article`), độ dài đủ tối thiểu (`>= 50 từ`), có tiêu đề và mốc thời gian xuất bản nằm trong phạm vi theo dõi (7 ngày gần nhất).

#### Giai đoạn 4: Data Collection (Thu thập và tích hợp dữ liệu)

- **Công cụ & Cơ chế:** `Step1_RawCrawler.py` sử dụng thư viện `requests` và `BeautifulSoup` để quét toàn bộ RSS feeds và tải HTML từng bài viết.
- **Cơ chế an toàn (Data Ingestion Safety):** Đặt độ trễ ngắt quãng `REQUEST_DELAY = 0.5s` cùng bộ header giả lập User-Agent của trình duyệt để ngăn ngừa chặn kết nối HTTP 429 hoặc IP ban.
- **Kết quả đầu ra:** Toàn bộ dữ liệu bóc tách được lưu vào tệp dữ liệu thô `vnexpress_raw.json` (Raw Dataset).

#### Giai đoạn 5: Data Understanding / EDA (Thấu hiểu và khám phá dữ liệu)

- **Khám phá cấu trúc:** Truy vấn dữ liệu từ CSDL Microsoft SQL Server vào DataFrame (`pandas`), kiểm tra các phân phối giá trị, giá trị thiếu (`Missing values`), bản ghi trùng lặp (`Duplicate`) và bài viết bất thường (`Outliers`).
- **Visualizations (Hệ thống biểu đồ phân tích):**
  - Phân tích cơ cấu số bài theo chuyên mục (`bieu_do_1_chuyen_muc.png`).
  - Phân tích chu kỳ nhịp điệu xuất bản 24 giờ (`bieu_do_2_phan_bo_gio.png`).
  - Phân tích cơ cấu tác giả tin tức (`bieu_do_3_tac_gia.png`).
  - Phân tích mật độ xuất bản theo thời gian thực dạng ô lịch (`bieu_do_4_nhiet_do_thang.png`).
- **Quyết định kiểm định (Data Quality Gate):**
  - *Nếu dữ liệu chưa đủ tốt hoặc phát hiện nhiều dữ liệu bẩn / thiếu hụt:* Quay lại bước **Data Requirements / Data Collection** để cào bổ sung hoặc điều chỉnh cấu trúc bóc tách.
  - *Nếu dữ liệu đạt chuẩn:* Chuyển sang giai đoạn **Data Preparation**.

#### Giai đoạn 6: Data Preparation (Chuẩn bị và làm sạch dữ liệu)

- **Cleaning & Post-processing (`Step2_DataFilter.py`):** Lọc bỏ các bài thiếu trường thông tin quan trọng, loại bỏ nội dung video/ảnh dạng đa phương tiện không có văn bản và khử khoảng trắng thừa.
- **Lưu trữ CSDL chuẩn hóa (`Phase 2 - SQLimporter.py`):** Nạp dữ liệu vào bảng `dbo.VnExpress_Articles` trên Microsoft SQL Server với cơ chế khử trùng lặp 2 lớp (trong batch và đối chiếu Primary Key trong CSDL).
- **Text Preprocessing & Feature Engineering (`TrainClassifier.py`):**
  - *Text Cleaning:* Chuyển chữ thường, loại bỏ URL, số hiệu, ký tự đặc biệt, chuẩn hóa hệ thống nguyên âm tiếng Việt có dấu.
  - *Text Representation (Encoding):* Nối liền `title + description + content` để nắm bắt ngữ cảnh trọn vẹn; chuyển đổi văn bản sang vector số học bằng **TF-IDF Vectorizer** (N-gram 1 đến 2, `max_features = 4000`, `sublinear_tf = True`).
- **Phân tách tập dữ liệu (Data Splitting - Gate 1 chống Data Leakage):**
  - Phân chia 80% tập huấn luyện (Train set) và 20% tập kiểm tra độc lập (Test set).
  - Áp dụng kỹ thuật **Stratified Sampling** dựa trên nhãn chuyên mục để đảm bảo tỷ lệ phân bố nhãn đồng nhất giữa hai tập dữ liệu.

#### Giai đoạn 7: Modeling (Xây dựng mô hình)

- **Thuật toán chính:** **Decision Tree Classifier (Cây quyết định)**:
  - Sử dụng tiêu chí phân chia Gini (`criterion='gini'`).
  - Kiểm soát độ sâu tối đa (`max_depth=25`) và số lượng mẫu tối thiểu để phân tách nhánh (`min_samples_split=4`) nhằm kiểm soát hiện tượng quá khớp (Overfitting).
- **Mô hình đối chứng (Baseline Model):** **Multinomial Naive Bayes** với hệ số làm mịn Laplace `alpha=0.1`.
- **Model Comparison:** So sánh trực tiếp hiệu năng giữa 2 mô hình học máy trên cùng tập vector hóa độc lập.

#### Giai đoạn 8: Evaluation (Đánh giá mô hình)

- **Các thước đo chẩn đoán (Diagnostic Measures):**
  - **Accuracy:** Đánh giá tổng quát tỷ lệ dự đoán chính xác trên toàn bộ các chuyên mục.
  - **Precision, Recall, F1-Score:** Đánh giá độ chính xác và độ bao phủ chi tiết cho từng chuyên mục riêng biệt qua `classification_report`.
  - **Confusion Matrix (Ma trận nhầm lẫn):** Vẽ Heatmap trực quan `confusion_matrix.png` để phát hiện các cặp chuyên mục thường bị nhầm lẫn ngữ nghĩa (ví dụ: *Thời sự* với *Xã hội*, *Kinh doanh* với *Bất động sản*).
  - **Feature Importance:** Trích xuất Top 15 từ khóa có trọng số Gini cao nhất trong Cây quyết định để giải thích tính logic của mô hình.
- **Tiêu chí thành công (Success Criteria Check):**
  - *Nếu mô hình không đạt tiêu chí:* Quay lại Giai đoạn 1 & 2 để định nghĩa lại bài toán hoặc điều chỉnh chiến lược trích xuất đặc trưng.
  - *Nếu mô hình đạt chuẩn:* Đóng gói mô hình (`joblib`) và chuyển sang Giai đoạn 9.

#### Giai đoạn 9: Deployment, Feedback & Monitoring (Triển khai, giám sát và vận hành)

- **Deployment (Triển khai):**
  - Lưu trữ mô hình và vectorizer vào tệp `.joblib` kèm hàm phụ trợ `predict_article_category()` sẵn sàng tích hợp vào API hoặc dịch vụ dán nhãn tự động.
  - Xuất báo cáo EDA trực quan và các tệp JSON số liệu đánh giá (`evaluation_metrics.json`).
- **Feedback & Monitoring (Vận hành & Giám sát):**
  - Module tự động hóa `Automation/Automation.py` điều phối thực thi trọn vẹn chuỗi 5 bước khép kín: *Cào mới -> Lọc sạch -> Huấn luyện cập nhật model -> Nạp SQL -> Cập nhật biểu đồ EDA*.
  - Ghi nhật ký vận hành vào `scheduler.log` để theo dõi tiến độ, kiểm soát tình trạng lỗi và đảm bảo tính toàn vẹn dữ liệu.

---

### 1.2. Kiến trúc luồng thực thi dự án

Sơ đồ kết nối giữa các module mã nguồn trong dự án:

```
[Phase 1: Raw Crawler -> Data Filter] ──(Dữ liệu cào JSON)
                 │
                 └───> [Phase 2: SQL importer] ───> [SQL Server: ADY201m] ───> [Phase 3: EDA]
                 [Train model] (Huấn luyện & Đánh giá độc lậ
```

![Sơ đồ luồng xử lý dữ liệu](<Vietnamese Data Workflow Pipeline.png>)

### 1.3. Ý nghĩa thực tiễn của mô tả dữ liệu

**Ứng dụng theo lĩnh vực:**

- **A. Báo chí và truyền thông:** theo dõi nhịp độ xuất bản theo giờ và chuyên mục; phân tích độ dài và đặc điểm nội dung; so sánh cơ cấu tin tức giữa các chuyên mục; làm nền cho việc theo dõi truyền thông và lập báo cáo truyền thông.
- **B. Phân tích xã hội:** theo dõi biến động các chủ đề kinh tế, giáo dục, y tế, môi trường và chính sách qua cơ cấu chuyên mục; phát hiện chủ đề mới hoặc tăng tần suất bất thường khi có chuỗi dữ liệu nhiều đợt cào; đối chiếu các nhận định về nội dung báo chí với số liệu thay vì dựa vào cảm nhận.
- **C. Kinh doanh và thị trường:** theo dõi các nhóm chủ đề Kinh doanh, Bất động sản và Khoa học công nghệ, hỗ trợ nghiên cứu thị trường và theo dõi tin liên quan đến ngành hoặc thương hiệu.
- **D. Y tế, khoa học và công nghệ:** theo dõi mức độ chú ý của truyền thông dành cho sức khỏe và công nghệ mới; so sánh chủ đề khoa học qua nhiều giai đoạn khi có thêm dữ liệu.
- **E. Giáo dục và nghiên cứu:** cung cấp bộ dữ liệu tiếng Việt có ghi rõ nguồn để thực hành thống kê mô tả, trực quan hóa, tái lập kết quả và mở rộng kho dữ liệu cho nghiên cứu tiếp theo.

### 1.4. Thu thập và làm sạch dữ liệu (`Phase 1 - Data crawl & Post process + Quick report`)

Tách bạch rõ ràng thành 2 bước độc lập:

1. **Bước 1 - Cào thô (`Step1_RawCrawler.py`):**
   - Quét toàn bộ RSS feeds của 16 chuyên mục chính của VnExpress trong 7 ngày gần nhất.
   - Cơ chế cào thô an toàn với `REQUEST_DELAY = 0.5s` để chống HTTP 429 / bot blocking.
   - Bóc tách đầy đủ 9 trường dữ liệu và lưu trọn vẹn vào `vnexpress_raw.json`.
2. **Bước 2 - Lọc dữ liệu (`Step2_DataFilter.py`):**
   - Kiểm tra chất lượng dữ liệu: bắt buộc có tiêu đề, đúng định dạng bài báo văn bản (`og:type = article`), loại bỏ bài quá ngắn (`< 50 từ`).
   - Xuất dữ liệu sạch sang `vnexpress_data.json` sẵn sàng nạp vào cơ sở dữ liệu.

### 1.5. Lưu trữ và khử trùng lặp (`Phase 2 - Import data to SQL`)

* **Mục tiêu:** Nạp dữ liệu từ file JSON vào Microsoft SQL Server, giữ tính toàn vẹn và tích lũy dữ liệu theo thời gian.
* **Luồng hoạt động (`SQLimporter.py`):**
  1. Tự động tìm và nạp file `vnexpress_data.json` từ Phase 1.
  2. Kiểm tra database `ADY201m` và bảng `dbo.VnExpress_Articles` qua kết nối ODBC (`.\SQLEXPRESS`).
  3. Khử trùng lặp 2 lớp: loại `article_id` trùng ngay trong file JSON và đối chiếu với tập `article_id` đã có trong CSDL để chỉ thêm bài mới.
  4. Nạp siêu tốc theo lô với `cursor.fast_executemany = True` cùng cơ chế phục hồi chèn từng dòng nếu gặp lỗi.
  5. Đi kèm script khởi tạo schema (`SQLschema.sql`) và script truy vấn mẫu (`DemoTruyVan.sql`).

### 1.6. Phân tích khám phá dữ liệu & Trực quan hóa (`Phase 3 - EDA`)

* **Mục tiêu:** Truy vấn dữ liệu trực tiếp từ SQL Server, tính các chỉ số thống kê mô tả và xuất ra 4 biểu đồ trực quan hóa dữ liệu (`Charts.py`).
* **Luồng hoạt động:**
  1. Kết nối SQL Server, tải các bản ghi đã lưu vào DataFrame của `pandas`.
  2. Tính độ dài bài viết (`word_count`), độ dài mô tả (`desc_wc`), lấy khung giờ xuất bản `hour` từ cột `published_at`.
  3. In bảng thống kê mô tả chi tiết bằng tiếng Việt ra console.
  4. Xuất 4 biểu đồ PNG trong `Phase 3 - EDA/`:
     - `bieu_do_1_chuyen_muc.png`: Cột ngang cơ cấu chuyên mục.
     - `bieu_do_2_phan_bo_gio.png`: Biểu đồ tần số xuất bản theo 24 khung giờ trong ngày.
     - `bieu_do_3_tac_gia.png`: Tỷ trọng tác giả VnExpress và nhóm tác giả khác.
     - `bieu_do_4_nhiet_do_thang.png`: Bản đồ nhiệt ma trận lịch tháng (Calendar Heatmap không trục) biểu thị mật độ bài viết theo độ đậm nhạt của màu sắc.

### 1.7. Huấn luyện và đánh giá mô hình phân loại tin tức (`Train model`)

* **Mục tiêu:** Nhận dữ liệu trực tiếp từ Phase 1 để huấn luyện mô hình phân loại chuyên mục tự động (`TrainClassifier.py`).
* **Luồng hoạt động:**
  1. Nạp trực tiếp dữ liệu từ file `vnexpress_data.json`.
  2. Chuẩn hóa văn bản tiếng Việt, phân chia Stratified Train/Test (80% train, 20% test).
  3. Trích xuất đặc trưng văn bản bằng `TfidfVectorizer` (N-gram 1-2).
  4. Huấn luyện mô hình **Cây quyết định (Decision Tree Classifier)** và Naive Bayes.
  5. Đánh giá chẩn đoán bằng `classification_report`, `accuracy_score` và xuất biểu đồ nhiệt ma trận nhầm lẫn `Train model/confusion_matrix.png`.
  6. Lưu trữ model (`category_classifier_model.joblib`) và bộ trích xuất đặc trưng (`tfidf_vectorizer.joblib`).

---

## 2. Thư viện Python sử dụng

| Thư viện                   | Chức năng trong dự án                                                                                    |
| :--------------------------- | :----------------------------------------------------------------------------------------------------------- |
| `requests`                 | Gửi yêu cầu HTTP tải nguồn tin RSS và trang bài viết từ VnExpress.                                  |
| `beautifulsoup4` (`bs4`) | Phân tích cú pháp HTML/XML, bóc tách 9 trường dữ liệu từ từng bài báo.                         |
| `pandas`                   | Cung cấp cấu trúc DataFrame, tính thống kê mô tả và thao tác dữ liệu.                            |
| `pyodbc`                   | Kết nối và thực thi câu lệnh SQL tới Microsoft SQL Server qua ODBC Driver.                            |
| `matplotlib`               | Vẽ các biểu đồ EDA và ma trận nhầm lẫn (Confusion Matrix).                                          |
| `scikit-learn`             | Trích xuất đặc trưng TF-IDF, huấn luyện Cây quyết định & Naive Bayes, tính chỉ số đánh giá. |
| `joblib`                   | Lưu trữ và tải lại mô hình học máy cùng vectorizer đã huấn luyện.                              |

---

## 3. Mô tả cấu trúc dữ liệu

Bảng **`dbo.VnExpress_Articles`** trên Microsoft SQL Server gồm 10 trường thông tin (9 trường bóc tách từ crawler + `created_at`):

| Tên cột        | Kiểu dữ liệu    | Ý nghĩa                                                   |
| :--------------- | :----------------- | :---------------------------------------------------------- |
| `article_id`   | `NVARCHAR(50)`   | Khóa chính — mã định danh bài báo                   |
| `title`        | `NVARCHAR(1000)` | Tiêu đề bài viết                                       |
| `description`  | `NVARCHAR(MAX)`  | Đoạn tóm tắt / sao-pô                                  |
| `content`      | `NVARCHAR(MAX)`  | Toàn văn nội dung bài viết                             |
| `author`       | `NVARCHAR(255)`  | Tên phóng viên / nguồn bài viết                       |
| `published_at` | `DATETIME`       | Thời gian xuất bản chuẩn hóa                           |
| `category`     | `NVARCHAR(100)`  | Chuyên mục chính (Kinh doanh, Thế giới, Sức khỏe...) |
| `subcategory`  | `NVARCHAR(100)`  | Chuyên mục phụ                                           |
| `url`          | `NVARCHAR(1000)` | Đường dẫn bài viết gốc                               |
| `created_at`   | `DATETIME`       | Thời gian hệ thống nạp bài vào CSDL                   |

---

## 4. Hướng dẫn cài đặt môi trường

### 4.1. Cài đặt Python và thư viện

1. Cài đặt **Python 3.11 hoặc 3.12** (chọn `Add python.exe to PATH`).
2. Cài đặt các thư viện cần thiết bằng một lệnh:
   ```powershell
   pip install -r requirements.txt
   ```

### 4.2. Cài đặt Microsoft SQL Server và SSMS

1. Cài đặt **SQL Server Express** (mặc định: `.\SQLEXPRESS`) và **SSMS**.
2. Khởi tạo cấu trúc database: mở file `Phase 2 - Import data to SQL/SQLschema.sql` trong SSMS và nhấn `F5` để tạo database `ADY201m` và bảng `dbo.VnExpress_Articles`.

---

## 5. Hướng dẫn vận hành hệ thống

### Cách 1: Chạy tự động chuỗi 5 bước khép kín (Khuyến nghị)

Chạy script điều phối tự động:

```powershell
python "Automation\Automation.py"
```

Hệ thống sẽ chạy trọn vẹn và tuần tự 5 bước theo chu trình Data Science:

1. `Step 1: Raw Crawler` (`Step1_RawCrawler.py`)
2. `Step 2: Data Filter` (`Step2_DataFilter.py`)
3. `Step 3: Train model` (`TrainClassifier.py`)
4. `Step 4: SQL importer` (`SQLimporter.py`)
5. `Step 5: EDA + charts` (`Charts.py`)

Sau khi chạy xong đủ 5 bước, script sẽ thông báo hoàn thành và tự động kết thúc. Toàn bộ tiến trình và thời gian chạy được lưu lại trong `scheduler.log`.

### Cách 2: Chạy thủ công từng bước

```powershell
# Bước 1: Cào dữ liệu thô từ 16 RSS feeds
python "Phase 1 - Data crawl & Post process + Quick report\Step1_RawCrawler.py"

# Bước 2: Lọc chất lượng dữ liệu
python "Phase 1 - Data crawl & Post process + Quick report\Step2_DataFilter.py"

# Bước 3: Nạp dữ liệu vào Microsoft SQL Server
python "Phase 2 - Import data to SQL\SQLimporter.py"

# Bước 4: Xuất thống kê mô tả và vẽ biểu đồ EDA
python "Phase 3 - EDA\Charts.py"

# Bước 5: Huấn luyện và đánh giá mô hình AI phân loại chuyên mục
python "Train model\TrainClassifier.py"
```
