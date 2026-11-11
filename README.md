# Báo cáo dự án nhóm 6 (Mô tả & Phân loại dữ liệu từ báo VnExpress)

Thành viên nhóm và phân công:

**Đinh Trung Hiếu**: phụ trách phân tích dữ liệu (EDA)

**Phạm Hùng Dương**: phụ trách web crawler

**Nguyễn Hữu Hùng**: phụ trách SQL & Tích hợp mô hình AI

---

## 1. Kiến trúc hệ thống

Hệ thống được thiết kế theo phương pháp luận Data Science của John Rollins, bao gồm chuỗi pipeline thu thập, làm sạch, lưu trữ, trực quan hóa và phân loại tự động:

```
[Phase 1: Raw Crawler -> Data Filter] ──(Dữ liệu cào JSON)──> [Train model] (Huấn luyện & Đánh giá độc lập)
                 │
                 └───> [Phase 2: SQL importer] ───> [SQL Server: ADY201m] ───> [Phase 3: EDA]
```

![Sơ đồ luồng xử lý dữ liệu](<Vietnamese Data Workflow Pipeline.png>)

### 1.1. Ý nghĩa thực tiễn của mô tả dữ liệu

**Ứng dụng theo lĩnh vực:**

- **A. Báo chí và truyền thông:** theo dõi nhịp độ xuất bản theo giờ và chuyên mục; phân tích độ dài và đặc điểm nội dung; so sánh cơ cấu tin tức giữa các chuyên mục; làm nền cho việc theo dõi truyền thông và lập báo cáo truyền thông.
- **B. Phân tích xã hội:** theo dõi biến động các chủ đề kinh tế, giáo dục, y tế, môi trường và chính sách qua cơ cấu chuyên mục; phát hiện chủ đề mới hoặc tăng tần suất bất thường khi có chuỗi dữ liệu nhiều đợt cào; đối chiếu các nhận định về nội dung báo chí với số liệu thay vì dựa vào cảm nhận.
- **C. Kinh doanh và thị trường:** theo dõi các nhóm chủ đề Kinh doanh, Bất động sản và Khoa học công nghệ, hỗ trợ nghiên cứu thị trường và theo dõi tin liên quan đến ngành hoặc thương hiệu.
- **D. Y tế, khoa học và công nghệ:** theo dõi mức độ chú ý của truyền thông dành cho sức khỏe và công nghệ mới; so sánh chủ đề khoa học qua nhiều giai đoạn khi có thêm dữ liệu.
- **E. Giáo dục và nghiên cứu:** cung cấp bộ dữ liệu tiếng Việt có ghi rõ nguồn để thực hành thống kê mô tả, trực quan hóa, tái lập kết quả và mở rộng kho dữ liệu cho nghiên cứu tiếp theo.

### 1.2. Thu thập và làm sạch dữ liệu (`Phase 1 - Data crawl & Post process + Quick report`)

Tách bạch rõ ràng thành 2 bước độc lập:
1. **Bước 1 - Cào thô (`Step1_RawCrawler.py`):**
   - Quét toàn bộ RSS feeds của 16 chuyên mục chính của VnExpress trong 7 ngày gần nhất.
   - Cơ chế cào thô an toàn với `REQUEST_DELAY = 0.5s` để chống HTTP 429 / bot blocking.
   - Bóc tách đầy đủ 9 trường dữ liệu và lưu trọn vẹn vào `vnexpress_raw.json`.
2. **Bước 2 - Lọc dữ liệu (`Step2_DataFilter.py`):**
   - Kiểm tra chất lượng dữ liệu: bắt buộc có tiêu đề, đúng định dạng bài báo văn bản (`og:type = article`), loại bỏ bài quá ngắn (`< 50 từ`).
   - Xuất dữ liệu sạch sang `vnexpress_data.json` sẵn sàng nạp vào cơ sở dữ liệu.

### 1.3. Lưu trữ và khử trùng lặp (`Phase 2 - Import data to SQL`)

* **Mục tiêu:** Nạp dữ liệu từ file JSON vào Microsoft SQL Server, giữ tính toàn vẹn và tích lũy dữ liệu theo thời gian.
* **Luồng hoạt động (`SQLimporter.py`):**
  1. Tự động tìm và nạp file `vnexpress_data.json` từ Phase 1.
  2. Kiểm tra database `ADY201m` và bảng `dbo.VnExpress_Articles` qua kết nối ODBC (`.\SQLEXPRESS`).
  3. Khử trùng lặp 2 lớp: loại `article_id` trùng ngay trong file JSON và đối chiếu với tập `article_id` đã có trong CSDL để chỉ thêm bài mới.
  4. Nạp siêu tốc theo lô với `cursor.fast_executemany = True` cùng cơ chế phục hồi chèn từng dòng nếu gặp lỗi.
  5. Đi kèm script khởi tạo schema (`SQLschema.sql`) và script truy vấn mẫu (`DemoTruyVan.sql`).

### 1.4. Phân tích khám phá dữ liệu & Trực quan hóa (`Phase 3 - EDA`)

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

### 1.5. Huấn luyện và đánh giá mô hình phân loại tin tức (`Train model`)

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

| Thư viện | Chức năng trong dự án |
| :--- | :--- |
| `requests` | Gửi yêu cầu HTTP tải nguồn tin RSS và trang bài viết từ VnExpress. |
| `beautifulsoup4` (`bs4`) | Phân tích cú pháp HTML/XML, bóc tách 9 trường dữ liệu từ từng bài báo. |
| `pandas` | Cung cấp cấu trúc DataFrame, tính thống kê mô tả và thao tác dữ liệu. |
| `pyodbc` | Kết nối và thực thi câu lệnh SQL tới Microsoft SQL Server qua ODBC Driver. |
| `matplotlib` | Vẽ các biểu đồ EDA và ma trận nhầm lẫn (Confusion Matrix). |
| `scikit-learn` | Trích xuất đặc trưng TF-IDF, huấn luyện Cây quyết định & Naive Bayes, tính chỉ số đánh giá. |
| `joblib` | Lưu trữ và tải lại mô hình học máy cùng vectorizer đã huấn luyện. |

---

## 3. Mô tả cấu trúc dữ liệu

Bảng **`dbo.VnExpress_Articles`** trên Microsoft SQL Server gồm 10 trường thông tin (9 trường bóc tách từ crawler + `created_at`):

| Tên cột | Kiểu dữ liệu | Ý nghĩa |
| :--- | :--- | :--- |
| `article_id` | `NVARCHAR(50)` | Khóa chính — mã định danh bài báo |
| `title` | `NVARCHAR(1000)` | Tiêu đề bài viết |
| `description` | `NVARCHAR(MAX)` | Đoạn tóm tắt / sao-pô |
| `content` | `NVARCHAR(MAX)` | Toàn văn nội dung bài viết |
| `author` | `NVARCHAR(255)` | Tên phóng viên / nguồn bài viết |
| `published_at` | `DATETIME` | Thời gian xuất bản chuẩn hóa |
| `category` | `NVARCHAR(100)` | Chuyên mục chính (Kinh doanh, Thế giới, Sức khỏe...) |
| `subcategory` | `NVARCHAR(100)` | Chuyên mục phụ |
| `url` | `NVARCHAR(1000)` | Đường dẫn bài viết gốc |
| `created_at` | `DATETIME` | Thời gian hệ thống nạp bài vào CSDL |

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

### Cách 1: Chạy tự động chuỗi 5 bước định kỳ (Khuyến nghị)
Chạy script điều phối tự động:
```powershell
python "Automation\Automation.py"
```
Hệ thống sẽ chạy tuần tự 5 bước:
1. `Step 1: Raw Crawler` (`Step1_RawCrawler.py`)
2. `Step 2: Data Filter` (`Step2_DataFilter.py`)
3. `Step 3: Train model` (`TrainClassifier.py`)
4. `Step 4: SQL importer` (`SQLimporter.py`)
5. `Step 5: EDA + charts` (`Charts.py`)

Chuỗi chạy lặp lại định kỳ mỗi 30 phút một lần, nhật ký lưu trong `scheduler.log`.

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
