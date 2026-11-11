# Báo cáo dự án nhóm 6 (Mô tả & Phân loại dữ liệu từ báo VnExpress)

Thành viên nhóm và phân công:

**Đinh Trung Hiếu**: phụ trách phân tích dữ liệu (EDA)

**Phạm Hùng Dương**: phụ trách web crawler

**Nguyễn Hữu Hùng**: phụ trách SQL & Tích hợp mô hình AI

---

## 1. Kiến trúc hệ thống

Hệ thống được thiết kế theo phương pháp luận Data Science của John Rollins, bao gồm luồng thu thập, xử lý phân loại tự động và lưu trữ:

```
[Web crawler] ──(Dữ liệu cào JSON/CSV)──> [AI classifier] (Phase 7 & 8: Train & Evaluate độc lập)
      │
      └───> [SQL importer] ───> [SQL Server: ADY201m] ───> [EDA + charts]
```

![Sơ đồ 3 bước: Web crawler → SQL importer → EDA + charts](<Vietnamese%20Data%20Workflow%20Pipeline.png>)

### 1.1. Ý nghĩa thực tiễn của mô tả dữ liệu

**Ứng dụng theo lĩnh vực:**

- **A. Báo chí và truyền thông:** theo dõi nhịp độ xuất bản theo giờ và chuyên mục; phân tích độ dài và đặc điểm nội dung; so sánh cơ cấu tin tức giữa các chuyên mục; làm nền cho việc theo dõi truyền thông và lập báo cáo truyền thông.
- **B. Phân tích xã hội:** theo dõi biến động các chủ đề kinh tế, giáo dục, y tế, môi trường và chính sách qua cơ cấu chuyên mục; phát hiện chủ đề mới hoặc tăng tần suất bất thường khi có chuỗi dữ liệu nhiều đợt cào; đối chiếu các nhận định về nội dung báo chí với số liệu thay vì dựa vào cảm nhận.
- **C. Kinh doanh và thị trường:** theo dõi các nhóm chủ đề Kinh doanh, Bất động sản và Khoa học công nghệ, hỗ trợ nghiên cứu thị trường và theo dõi tin liên quan đến ngành hoặc thương hiệu. Các phát hiện chỉ nên dùng để xây dựng giả thuyết, không tự động coi là kết luận kinh doanh.
- **D. Y tế, khoa học và công nghệ:** theo dõi mức độ chú ý của truyền thông dành cho sức khỏe và công nghệ mới; so sánh chủ đề khoa học qua nhiều giai đoạn khi có thêm dữ liệu.
- **E. Giáo dục và nghiên cứu:** cung cấp bộ dữ liệu tiếng Việt có ghi rõ nguồn để thực hành thống kê mô tả, trực quan hóa, tái lập kết quả và mở rộng kho dữ liệu cho nghiên cứu tiếp theo.

*Lưu ý:* biểu đồ khung giờ phản ánh mẫu cào tại thời điểm chạy, không đại diện cho nhịp xuất bản trong ngày.

### 1.2. Thu thập và làm sạch dữ liệu tại nguồn (`CustomCrawler`)

* **Mục tiêu:** Thu thập bài viết đa luồng từ 16 chuyên mục chính của VnExpress (qua RSS và quét phân trang danh mục), làm sạch và kiểm tra hợp lệ ngay khi bóc tách. Bản cũ dạng tuần tự đơn kênh đã được lưu trữ an toàn tại Web crawler/archive/Webcrawler_legacy.py.
* **Luồng hoạt động:**
  1. Gửi yêu cầu HTTP tải danh sách bài viết mới từ nguồn tin RSS (`https://vnexpress.net/rss/tin-moi-nhat.rss`) bằng thư viện `requests` và bộ phân tích XML `lxml`. Các yêu cầu đi qua hàm `fetch()` có gọi `raise_for_status()` (bắt lỗi 4xx/5xx để không nạp trang rác) và đặt `encoding = "utf-8"`.
  2. Truy cập vào từng liên kết bài viết (nghỉ `CRAWL_DELAY` = 1.0s giữa các yêu cầu), kiểm tra `is_article_page()` trước khi bóc tách: `og:type` cần là `article` (nếu trang có khai báo) và trang cần có thẻ `h1`. Trang video/clip/album (`og:type = website`, không có `h1`) bị loại, không đưa vào dữ liệu.
  3. Bóc tách 9 trường dữ liệu (`article_id`, `title`, `description`, `content`, `author`, `published_at`, `category`, `subcategory`, `url`) bằng `BeautifulSoup`, làm sạch ngay trong lúc bóc:
     - Cắt khoảng trắng thừa (`.strip()`) và bỏ các đoạn văn rỗng.
     - `extract_paragraphs()` thử nhiều bộ chọn dự phòng (`.fck_detail p.Normal` → `.fck_detail p` → ...) và chọn bộ chọn đầu tiên cho từ 2 đoạn có chữ trở lên.
     - Tách chữ ký tác giả in đậm (`<strong>`) ở đoạn cuối ra khỏi `content` để lưu vào cột `author`.
     - `normalize_datetime()` đọc được cả chuỗi tiếng Việt và chuỗi ISO, chuyển về `YYYY-MM-DD HH:MM:SS`.
     - Tách `category`/`subcategory` từ dải liên kết chuyên mục ở đầu trang.
     - **Bộ lọc chất lượng:** bài thiếu `title` hoặc thiếu `content` bị loại.
  4. Đóng gói và lưu đồng thời ra 2 định dạng file tại thư mục `Web crawler/`: `vnexpress_data.json` và `vnexpress_data.csv`.

### 1.3. Huấn luyện và đánh giá mô hình phân loại tin tức (`AI classifier`)

* **Mục tiêu:** Thực hiện Phase 7 (Xây dựng Mô hình) và Phase 8 (Đánh giá Mô hình) theo chuẩn John Rollins, nhận dữ liệu trực tiếp từ bước Web crawler để huấn luyện mô hình phân loại chuyên mục mà không phụ thuộc vào CSDL.
* **Luồng hoạt động:**
  1. Nạp trực tiếp dữ liệu thô từ file CSV/JSON do `Web crawler` tạo ra.
  2. Chuẩn hóa văn bản tiếng Việt: làm sạch URL, ký tự đặc biệt, ghép nối `title + description + content`.
  3. Phân chia tập dữ liệu độc lập (Stratified Train/Test Split: 80% train, 20% test) nhằm bảo vệ tính toàn vẹn (Quality Gate 1 - chống data leakage).
  4. Trích xuất đặc trưng văn bản bằng `TfidfVectorizer` (N-gram 1-2, sublinear TF scaling).
  5. Huấn luyện mô hình chủ đạo **Cây quyết định (Decision Tree Classifier)** phù hợp môi trường CPU, tính minh bạch cao, giải thích rõ ràng các nhánh điều kiện phân loại và top đặc trưng quan trọng nhất (Quality Gate 3).
  6. Đánh giá chẩn đoán (Diagnostic Measures - Quality Gate 2) bằng `classification_report`, `accuracy_score` và xuất biểu đồ nhiệt ma trận nhầm lẫn `AI classifier/confusion_matrix.png`.
  7. Cung cấp hàm `predict_article_category` cho phép phân loại tự động bài viết mới chưa dán nhãn.

### 1.4. Lưu trữ và khử trùng lặp (`SQL importer`)

* **Mục tiêu:** Nạp dữ liệu từ file JSON vào Microsoft SQL Server, giữ tính toàn vẹn và tích lũy dữ liệu theo thời gian.
* **Luồng hoạt động:**
  1. Tìm và nạp file `vnexpress_data.json` từ thư mục `Web crawler/`.
  2. Kiểm tra database `ADY201m` và bảng `dbo.VnExpress_Articles` qua kết nối ODBC.
  3. Khử trùng lặp hai bước: loại `article_id` trùng ngay trong file JSON và đối chiếu với tập `article_id` đã có trong CSDL để chỉ giữ bài mới.
  4. Nạp theo lô bằng `executemany` với `fast_executemany = True` cùng cơ chế fallback chèn từng dòng nếu gặp lỗi.

### 1.5. Mô tả dữ liệu và trực quan hóa (`EDA + charts`)

* **Mục tiêu:** Truy vấn dữ liệu trực tiếp từ SQL Server, tính các chỉ số thống kê mô tả và xuất ra 4 biểu đồ trực quan hóa dữ liệu.
* **Luồng hoạt động:**
  1. Kết nối SQL Server, tải các bản ghi đã lưu vào DataFrame của `pandas`.
  2. Tính độ dài bài viết (`word_count`), độ dài mô tả (`desc_wc`), lấy khung giờ xuất bản `hour` từ cột `published_at`.
  3. In bảng thống kê mô tả chi tiết bằng tiếng Việt ra console.
  4. Xuất 4 biểu đồ PNG trong `EDA + charts/`: `bieu_do_1_chuyen_muc.png`, `bieu_do_2_phan_bo_gio.png`, `bieu_do_3_tac_gia.png`, `bieu_do_4_nhiet_do_chuyen_muc_gio.png`.

---

## 2. Thư viện Python sử dụng

| Thư viện | Chức năng trong dự án |
| :--- | :--- |
| `requests` | Gửi yêu cầu HTTP tải nguồn tin RSS và trang bài viết từ VnExpress. |
| `beautifulsoup4` (`bs4`) | Phân tích cú pháp HTML/XML, bóc tách 9 trường dữ liệu từ từng bài báo. |
| `lxml` | Bộ phân tích XML làm backend cho BeautifulSoup khi đọc RSS. |
| `pandas` | Cung cấp cấu trúc DataFrame, tính thống kê mô tả và thao tác dữ liệu. |
| `pyodbc` | Kết nối và thực thi câu lệnh SQL tới Microsoft SQL Server qua ODBC Driver. |
| `matplotlib` | Vẽ 4 biểu đồ EDA và ma trận nhầm lẫn (Confusion Matrix). |
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

## 4. Báo cáo thống kê mô tả & Đánh giá mô hình

![Bảng tóm tắt 4 biểu đồ EDA](<Vietnamese%20Data%20Table.png>)

### 4.1. Biểu đồ 1 — Số bài theo chuyên mục (biểu đồ cột ngang)
* **Dạng:** Cột ngang sắp xếp tăng dần, hiển thị số bài kèm % trên tổng số mẫu; tô màu theo thang 20 bậc.
* **Trường dữ liệu:** `category`.

### 4.2. Biểu đồ 2 — Số bài xuất bản theo 24 khung giờ (biểu đồ tần số)
* **Dạng:** Biểu đồ tần số 24 cột tương ứng 24 khung giờ trong ngày (0h–23h), màu động theo tần số.
* **Trường dữ liệu:** `published_at` → `hour`.

### 4.3. Biểu đồ 3 — Cơ cấu tác giả bài viết (biểu đồ tròn)
* **Dạng:** Biểu đồ tròn hai phần: `VnExpress` (xanh) và Các tác giả khác (xám).
* **Trường dữ liệu:** `author`.

### 4.4. Biểu đồ 4 — Số bài theo chuyên mục và khung giờ xuất bản (bản đồ nhiệt)
* **Dạng:** Bản đồ nhiệt chuyên mục × 24 khung giờ, có số lượng bài trực quan trên từng ô.
* **Trường dữ liệu:** `category` × `hour`.

### 4.5. Quy ước màu dùng chung
* Bảng **20 màu rời, cách đều**: xanh biển `#1f78b4` → xanh ngọc → xanh lá → vàng → cam → đỏ `#e31a1c`.
* Hàm `mau_theo_gia_tri(values)` ánh xạ mỗi giá trị về một bậc rời trên thang màu.

### 4.6. Giới hạn chung khi đọc kết quả
- Một số bài không có `subcategory` (ghi "Không có") và các nhãn chuyên mục con phân bố mỏng, nên không dùng để phân tích sâu.
- Tên tác giả mặc định `"VnExpress"` là quy ước của crawler để gắn trường tác giả cho những bài không có tác giả cụ thể.

### 4.7. Đánh giá mô hình phân loại tin tức AI (`AI classifier`)
* **Ma trận nhầm lẫn (Confusion Matrix):** Lưu tại `AI classifier/confusion_matrix.png`, thể hiện mức độ phân loại chính xác giữa nhãn thực tế và nhãn dự đoán trên 16 chuyên mục.
* **Top đặc trưng phân loại:** Mô hình Cây quyết định tự động trích xuất các từ khóa đặc trưng có trọng số phân loại cao nhất (như *bệnh, cầu thủ, chiến, doanh nghiệp, xe, công an, dự án...*), giúp bác bỏ tính "hộp đen" và nâng cao khả năng giải thích của mô hình.
* **Chỉ số đánh giá:** Lưu trữ tự động tại `AI classifier/evaluation_metrics.json` gồm `accuracy`, `precision`, `recall`, `f1-score`.

---

## 5. Hướng dẫn cài đặt môi trường

### 5.1. Cài đặt Python và thư viện

1. Cài đặt **Python 3.11 hoặc 3.12** (nhớ tích chọn `Add python.exe to PATH`).
2. Cài đặt các thư viện cần thiết bằng một lệnh:
   ```powershell
   pip install -r requirements.txt
   ```

### 5.2. Cài đặt Microsoft SQL Server và SSMS

1. Cài đặt **SQL Server Express** (mặc định: `.\SQLEXPRESS`) và **SSMS**.
2. Khởi tạo cấu trúc database: mở file `SQL importer/SQLschema.sql` trong SSMS và nhấn `F5` để tạo database `ADY201m` và bảng `dbo.VnExpress_Articles`.

---

## 6. Hướng dẫn vận hành hệ thống

### Cách 1: Chạy tự động toàn bộ 4 bước định kỳ (Khuyến nghị)
Chạy script điều phối tự động:
```powershell
python "Automation\Automation.py"
```
Hệ thống sẽ chạy liên hoàn 4 bước (Web crawler → AI classifier → SQL importer → EDA + charts) và lặp lại mỗi 30 phút một lần. Nhật ký chạy được lưu trong `scheduler.log`.

### Cách 2: Chạy thủ công từng bước

```powershell
# Bước 1: Thu thập bài báo mới từ RSS VnExpress
python "Web crawler\CustomCrawler.py"

# Bước 2: Huấn luyện và đánh giá mô hình AI phân loại chuyên mục
python "AI classifier\TrainClassifier.py"

# Bước 3: Nạp dữ liệu vào Microsoft SQL Server
python "SQL importer\SQLimporter.py"

# Bước 4: Xuất thống kê mô tả và vẽ 4 biểu đồ EDA
python "EDA + charts\Charts.py"
```


---

## 7. Khởi chạy Jupyter Notebook nghiên cứu (`notebooks/ADY201m_Data_Analysis.ipynb`)

Sổ tay phân tích khoa học dữ liệu hoàn chỉnh của môn học được lưu tại `notebooks/ADY201m_Data_Analysis.ipynb`.

### 7.1. Cài đặt môi trường cho Jupyter Notebook
Đảm bảo đã cài đặt đầy đủ các thư viện từ file `requirements.txt`:
```powershell
pip install -r requirements.txt
pip install jupyter
```

### 7.2. Khởi động và thực thi Notebook
Khởi chạy Jupyter Notebook hoặc JupyterLab từ thư mục gốc của dự án:
```powershell
jupyter notebook notebooks/ADY201m_Data_Analysis.ipynb
# Hoặc mở toàn bộ thư mục bằng JupyterLab:
jupyter lab
```

### 7.3. Đặc điểm thực thi của Notebook:
* **Tương thích nguồn đa tầng (Fallback Strategy)**: Tự động ưu tiên đọc từ kho dữ liệu tích lũy trên Microsoft SQL Server (`dbo.VnExpress_Articles`). Nếu máy trạm chưa cài đặt hoặc chưa mở SQL Server, notebook tự động chuyển sang đọc dữ liệu thực từ tệp `Web crawler/vnexpress_data.csv` hoặc `vnexpress_data.json` mà không gây ra bất kỳ lỗi gián đoạn nào.
* **Quy trình 11 giai đoạn chuẩn Data Science**: Đi từ Tổng quan dự án, Đánh giá chất lượng dữ liệu, Kỹ thuật đặc trưng, EDA trực quan hóa, Kiểm định thống kê toán học (Kruskal-Wallis, Spearman correlation), đến Huấn luyện mô hình AI (Decision Tree & Naive Bayes) và Đúc kết giá trị thực tiễn.
* **Tính độc lập và toàn vẹn**: 100% các biến và thư viện được khai báo tuần tự, không có biến ẩn hay phụ thuộc cache, đảm bảo chạy thành công 100% từ đầu đến cuối với thao tác **Restart Kernel & Run All Cells**.
