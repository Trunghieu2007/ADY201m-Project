# Báo cáo dự án nhóm 6 (Mô tả dữ liệu từ báo VNExpress)

Thành viên nhóm và phân công:

**Đinh Trung Hiếu**:

**Phạm Hùng Dương**:

**Nguyễn Hữu Hùng**:

---

## 1. Kiến trúc hệ thống

Hệ thống được thiết kế theo mô hình 3 bước:

```
[1. Web crawler]                 [2. SQL importer]                [3. EDA + charts]
  Webcrawler.py       ───►         SQLimporter.py        ───►       Charts.py
  (Cào tin RSS + lọc và            (Nạp dữ liệu đã xử lý         (Query SQL, thống kê &
   bóc tách 9 trường)                vào SQL Server )             xuất 4 ảnh PNG)
         │                                 │                               │
         ▼                                 ▼                               ▼
vnexpress_data.json              dbo.VnExpress_Articles          bieu_do_1..4_*.png
vnexpress_data.csv               (Database: ADY201m)
```

### 1.1. Ý nghĩa thực tiễn của mô tả dữ liệu

**Ứng dụng theo lĩnh vực:**

- **A. Báo chí và truyền thông:** theo dõi nhịp độ xuất bản theo giờ và chuyên mục; phân tích độ dài và đặc điểm nội dung; so sánh cơ cấu tin tức giữa các chuyên mục; làm nền cho hệ thống media monitoring và báo cáo truyền thông.
- **B. Phân tích xã hội:** theo dõi biến động các chủ đề kinh tế, giáo dục, y tế, môi trường và chính sách qua cơ cấu chuyên mục; phát hiện chủ đề mới hoặc tăng tần suất bất thường khi có chuỗi dữ liệu nhiều đợt cào; kiểm chứng các nhận định về nội dung báo chí bằng số liệu định lượng thay vì cảm nhận.
- **C. Kinh doanh và thị trường:** theo dõi các nhóm chủ đề Kinh doanh, Bất động sản và Khoa học công nghệ, hỗ trợ nghiên cứu thị trường và theo dõi tin liên quan đến ngành hoặc thương hiệu. Các phát hiện chỉ nên dùng để xây dựng giả thuyết, không tự động coi là kết luận kinh doanh.
- **D. Y tế, khoa học và công nghệ:** theo dõi mức độ chú ý của truyền thông dành cho sức khỏe và công nghệ mới; so sánh chủ đề khoa học qua nhiều giai đoạn khi có thêm dữ liệu.
- **E. Giáo dục và nghiên cứu:** cung cấp bộ dữ liệu tiếng Việt có nguồn gốc rõ ràng để thực hành thống kê mô tả, trực quan hóa, tái lập kết quả và mở rộng kho dữ liệu cho nghiên cứu tiếp theo.

*Lưu ý:* biểu đồ khung giờ phản ánh mẫu cào tại thời điểm chạy, không phải toàn bộ nhịp xuất bản trong ngày

### 1.2. Module Thu thập & Làm sạch dữ liệu tại nguồn (`Web crawler`)

* **Mục tiêu:** Thu thập các bài báo mới nhất từ RSS Feed của VnExpress và thực hiện làm sạch dữ liệu ngay trong quá trình bóc tách.
* **Luồng hoạt động:**
  1. Gửi HTTP Request tải danh sách bài viết mới từ RSS feed (`https://vnexpress.net/rss/tin-moi-nhat.rss`) bằng thư viện `requests` và parser XML `lxml`. Mọi request đều qua hàm `fetch()` gọi `raise_for_status()` (bắt lỗi 4xx/5xx để không nạp trang rác) và ép `encoding = "utf-8"`.
  2. Đọc `robots.txt` của miền để lấy danh sách đường dẫn bị cấm, lọc bỏ liên kết không phải bài báo chính thống (video, podcast, trang ảnh) và bỏ qua các URL bị `robots.txt` cấm.
  3. Truy cập vào từng liên kết bài viết (nghỉ `CRAWL_DELAY` = 1.0s giữa các request), dùng `BeautifulSoup` bóc tách 9 trường dữ liệu (`article_id`, `title`, `description`, `content`, `author`, `published_at`, `category`, `subcategory`, `url`).
  4. Làm sạch tại nguồn:
     - Cắt tỉa khoảng trắng thừa (`.strip()`), loại bỏ hoàn toàn các đoạn văn rỗng.
     - Bóc nội dung bằng `extract_paragraphs()` với nhiều selector dự phòng (`.fck_detail p.Normal` → `.fck_detail p` → ...) để không âm thầm mất nội dung khi VnExpress đổi markup.
     - Tách rời chữ ký tác giả in đậm (`<strong>`) ở cuối bài ra khỏi trường `content` để lưu đúng vào cột `author`.
     - `normalize_datetime()` bóc riêng ngày (`dd/mm/yyyy`) và giờ (`HH:mm`) từ chuỗi gốc `"Thứ bảy, 17/10/2026, 23:37 (GMT+7)"`, rồi ghép về chuẩn `YYYY-MM-DD HH:MM:SS` (bỏ được cả dấu phẩy và hậu tố GMT); thiếu giờ thì giờ = `00:00`, không parse được ngày thì để `null`.
     - Xử lý giá trị khuyết thiếu: Gán mặc định `"Không có"` cho tiểu mục, `"Khác"` cho chuyên mục, và `"VnExpress"` cho bài không đề tên tác giả.
  5. Đóng gói và lưu đồng thời ra 2 định dạng file tại thư mục `Web crawler/`:
     - `vnexpress_data.json`.
     - `vnexpress_data.csv`.

### 1.3. Module Lưu trữ & Khử trùng lặp (`SQL importer`)

* **Mục tiêu:** Nạp dữ liệu từ file JSON vào Microsoft SQL Server, duy trì tính toàn vẹn và tích lũy dữ liệu theo thời gian.
* **Luồng hoạt động:**
  1. Tự động tìm nạp file `vnexpress_data.json` từ thư mục `Web crawler/`.
  2. Kiểm tra Database thật: mở kết nối tới `master`, truy vấn `sys.databases` xem `ADY201m` đã tồn tại chưa. Nếu chưa, in thông báo yêu cầu người dùng chạy `SQL importer/SQLschema.sql` và dừng.
  3. Kiểm tra bảng: nối trực tiếp `ADY201m`, kiểm tra `dbo.VnExpress_Articles` qua `OBJECT_ID`. Nếu bảng chưa có, in thông báo nạp schema và **dừng** (giảm codebase — schema luôn do người dùng chạy bằng `SQLschema.sql`).
  4. Khử trùng lặp 2 tầng: trước hết loại `article_id` trùng ngay trong batch JSON (tránh vi phạm PRIMARY KEY), rồi đối chiếu với `set` các `article_id` đã có trong CSDL để chỉ giữ bài hoàn toàn mới.
  5. Nạp bằng `executemany` với `fast_executemany = True` (nhanh hơn chèn từng dòng). Trường `published_at` được ép về `datetime` để ghi vào cột `DATETIME`. Nếu lệnh chèn hàng loạt lỗi, tự động fallback chèn từng dòng trong `try/except`, để một dòng hỏng không phá cả batch, và in báo cáo số bài chèn được / thất bại.

### 1.4. Module Mô tả dữ liệu & Trực quan hóa (`EDA + charts`)

* **Mục tiêu:** Truy vấn dữ liệu trực tiếp từ SQL Server, tính toán các chỉ số thống kê mô tả và xuất ra 4 biểu đồ (mỗi biểu đồ 1 file PNG riêng).
* **Luồng hoạt động:**
  1. Mở kết nối tới SQL Server, dùng lệnh SQL `SELECT ... FROM dbo.VnExpress_Articles` để tải toàn bộ các bản ghi đã lưu vào DataFrame của `pandas`.
  2. Tiền xử lý đặc trưng cho EDA:
     - Tính toán độ dài số từ của bài viết (`word_count`) từ trường `content`.
     - Lấy khung giờ xuất bản (0h - 23h) trực tiếp từ cột `DATETIME` `published_at` bằng `pandas .dt.hour` (không còn parse chuỗi tiếng Việt mong manh như trước).
     - Chuẩn hóa nguồn bài viết thành biến phân loại nhị phân: `"Tác giả cụ thể"` vs `"Chung (VnExpress)"`.
  3. In các chỉ số thống kê mô tả ra terminal: tổng số bài, số bài có nội dung rỗng, count/mean/std/min/max cho `word_count` và `hour`, cùng tần số chuyên mục.
  4. Dùng `matplotlib` dựng 4 biểu đồ đơn biến, mỗi biểu đồ lưu thành 1 file PNG riêng trong `EDA + charts/` (`bieu_do_1_chuyen_muc.png` ... `bieu_do_4_khung_gio.png`), tô màu theo 20 bậc rời (thấp = xanh biển, giữa = xanh lá, cao = đỏ).

---

## 2. Thư viện Python sử dụng

| Thư viện                   | Chức năng trong dự án                                                                |
| :--------------------------- | :--------------------------------------------------------------------------------------- |
| `requests`                 | Gửi HTTP Request tải RSS Feed và trang bài viết từ VnExpress.                      |
| `beautifulsoup4` (`bs4`) | Phân tích cú pháp HTML/XML, bóc tách 9 trường dữ liệu từ từng bài báo.     |
| `lxml`                     | Parser XML tốc độ cao, được BeautifulSoup dùng làm backend khi đọc RSS Feed.   |
| `pandas`                   | Cấu trúc dữ liệu dạng DataFrame, tính toán thống kê mô tả và xuất file CSV. |
| `pyodbc`                   | Kết nối và thực thi câu lệnh SQL tới Microsoft SQL Server qua ODBC Driver.        |
| `matplotlib`               | Vẽ 4 biểu đồ trực quan hóa và xuất ra 4 file ảnh PNG.                           |

---

## 3. Mô tả cấu trúc dữ liệu

Bảng **`dbo.VnExpress_Articles`** trên Microsoft SQL Server lưu trữ 10 trường thông tin (9 trường bóc tách từ crawler + `created_at`):

| Tên cột        | Kiểu dữ liệu    | Ý nghĩa                                                         |
| :--------------- | :----------------- | :---------------------------------------------------------------- |
| `article_id`   | `NVARCHAR(50)`   | **Khóa chính (Primary Key)** — Mã định danh bài báo |
| `title`        | `NVARCHAR(1000)` | Tiêu đề bài viết                                             |
| `description`  | `NVARCHAR(MAX)`  | Đoạn tóm tắt / Sa-pô                                         |
| `content`      | `NVARCHAR(MAX)`  | Toàn bộ nội dung văn bản (Full text)                         |
| `author`       | `NVARCHAR(255)`  | Tên phóng viên / Nguồn bài viết                             |
| `published_at` | `DATETIME`       | Thời gian xuất bản (đã ép về chuẩn datetime từ crawler)  |
| `category`     | `NVARCHAR(100)`  | Chuyên mục chính (Kinh doanh, Thế giới, Sức khỏe...)       |
| `subcategory`  | `NVARCHAR(100)`  | Chuyên mục phụ                                                 |
| `url`          | `NVARCHAR(1000)` | Đường dẫn bài viết gốc                                     |
| `created_at`   | `DATETIME`       | Thời gian hệ thống nạp bài vào CSDL                         |

---

## 4. Báo cáo thống kê mô tả dữ liệu

Toàn bộ dữ liệu được truy vấn trực tiếp từ SQL Server và trực quan hóa thành 4 biểu đồ, mỗi biểu đồ xuất ra 1 file PNG riêng:

1. **Biểu đồ 1: Phân bố số lượng bài theo chuyên mục (Bar Chart)**
2. **Biểu đồ 2: Hình thái phân bố độ dài bài báo (Histogram)**
3. **Biểu đồ 3: Tỷ lệ nguồn tác giả (Donut Chart)**
4. **Biểu đồ 4: Phân bố theo 24 khung giờ xuất bản (Bar Chart)**

---

## 5. Hướng dẫn cài đặt môi trường

### 5.1. Cài đặt Python & Thư viện

1. Cài đặt **Python 3.11 hoặc 3.12** (Lưu ý tích chọn `Add python.exe to PATH`).
2. Cài đặt toàn bộ thư viện (đã pin phiên bản trong `requirements.txt`) bằng 1 câu lệnh duy nhất:
   ```powershell
   pip install -r requirements.txt
   ```

### 5.2. Cài đặt Microsoft SQL Server & SSMS

1. Cài đặt **SQL Server Express** (Instance mặc định: `.\SQLEXPRESS`) và **SSMS**.
2. **Bắt buộc khởi tạo schema trước khi nạp:** Mở file `SQL importer/SQLschema.sql` trong SSMS và nhấn `F5` để tạo Database `ADY201m` và bảng `dbo.VnExpress_Articles`. `SQLimporter.py` không tự tạo DB/bảng — nếu chưa có, nó sẽ in thông báo hướng dẫn chạy schema và dừng lại.
3. **Nâng cấp từ phiên bản cũ:** nếu bảng đã tồn tại với cột `published_at` kiểu `NVARCHAR` (dữ liệu lẫn lộn định dạng), hãy `DROP TABLE dbo.VnExpress_Articles;` rồi chạy lại `SQLschema.sql` để có cột `DATETIME` sạch, sau đó chạy lại 3 bước.

---

## 6. Hướng dẫn vận hành hệ thống

Mở Terminal tại thư mục gốc `ADY201m Final` và thực thi lần lượt 3 lệnh:

```powershell
# Bước 1: Thu thập dữ liệu báo chí mới nhất
python "Web crawler\Webcrawler.py"

# Bước 2: Nạp dữ liệu vào Microsoft SQL Server
python "SQL importer\SQLimporter.py"

# Bước 3: Xuất thống kê mô tả và vẽ 4 biểu đồ PNG
python "EDA + charts\Charts.py"
```
