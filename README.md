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
   bóc tách 9 trường)                vào SQL Server )             xuất 1 ảnh Dashboard)
         │                                 │                               │
         ▼                                 ▼                               ▼
vnexpress_data.json              dbo.VnExpress_Articles          tong_hop_4_bieu_do.png
vnexpress_data.csv               (Database: ADY201m)
```

### 1.1. Module Thu thập & Làm sạch dữ liệu tại nguồn (`Web crawler`)

* **Mục tiêu:** Thu thập các bài báo mới nhất từ RSS Feed của VnExpress và thực hiện làm sạch dữ liệu ngay trong quá trình bóc tách.
* **Luồng hoạt động:**
  1. Gửi HTTP Request tải danh sách bài viết mới từ RSS feed (`https://vnexpress.net/rss/tin-moi-nhat.rss`) bằng thư viện `requests` và parser XML `lxml`.
  2. Lọc bỏ các liên kết không phải bài báo chính thống (bỏ qua video, podcast, trang ảnh).
  3. Truy cập vào từng liên kết bài viết, dùng `BeautifulSoup` bóc tách 9 trường dữ liệu (`article_id`, `title`, `description`, `content`, `author`, `published_at`, `category`, `subcategory`, `url`).
  4. Làm sạch tại nguồn:
     - Cắt tỉa khoảng trắng thừa (`.strip()`), loại bỏ hoàn toàn các đoạn văn rỗng.
     - Tách rời chữ ký tác giả in đậm (`<strong>`) ở cuối bài ra khỏi trường `content` để lưu đúng vào cột `author`.
     - Xử lý giá trị khuyết thiếu: Gán mặc định `"Không có"` cho tiểu mục, `"Khác"` cho chuyên mục, và `"VnExpress"` cho bài không đề tên tác giả.
  5. Đóng gói và lưu đồng thời ra 2 định dạng file tại thư mục `Web crawler/`:
     - `vnexpress_data.json`.
     - `vnexpress_data.csv`.

### 1.2. Module Lưu trữ & Khử trùng lặp (`SQL importer`)

* **Mục tiêu:** Nạp dữ liệu từ file JSON vào Microsoft SQL Server, duy trì tính toàn vẹn và tích lũy dữ liệu theo thời gian.
* **Luồng hoạt động:**
  1. Tự động tìm nạp file `vnexpress_data.json` từ thư mục `Web crawler/`.
  2. Tự động kiểm tra Database `ADY201m`qua kết nối `master`, sau đó mở kết nối trực tiếp vào `ADY201m`.
  3. Kiểm tra và tự động khởi tạo bảng `dbo.VnExpress_Articles` cùng chỉ mục Index nếu bảng chưa tồn tại.
  4. Khử trùng lặp: Truy vấn toàn bộ `article_id` đã có trong CSDL đưa vào một Python `set`, sau đó lọc chỉ giữ lại những bài viết hoàn toàn mới (`new_articles`).
  5. Thực thi câu lệnh `INSERT` nạp các bài mới vào bảng, bỏ qua các bài đã có.

### 1.3. Module Mô tả dữ liệu & Trực quan hóa (`EDA + charts`)

* **Mục tiêu:** Truy vấn dữ liệu trực tiếp từ SQL Server, tính toán các chỉ số thống kê mô tả và xuất ra 1 Dashboard biểu đồ tổng hợp duy nhất.
* **Luồng hoạt động:**
  1. Mở kết nối tới SQL Server, dùng lệnh SQL `SELECT ... FROM dbo.VnExpress_Articles` để tải toàn bộ các bản ghi đã lưu vào DataFrame của `pandas`.
  2. Tiền xử lý đặc trưng cho EDA:
     - Tính toán độ dài số từ của bài viết (`word_count`) từ trường `content`.
     - Bóc tách khung giờ xuất bản (0h - 23h) từ chuỗi thời gian tiếng Việt `published_at` và ép về kiểu số nguyên (`int`).
     - Chuẩn hóa nguồn bài viết thành biến phân loại nhị phân: `"Tác giả cụ thể"` vs `"Chung (VnExpress)"`.
  3. In các chỉ số Thống kê mô tả (Count, Mean, Min, Max, Quantiles, Tần số chuyên mục) ra terminal.
  4. Dùng `matplotlib` dựng một Dashboard `2x2` gom 4 biểu đồ đơn biến vào 1 file ảnh duy nhất tại `EDA + charts/tong_hop_4_bieu_do.png`.

---

## 2. Mô tả cấu trúc dữ liệu

Bảng **`dbo.VnExpress_Articles`** trên Microsoft SQL Server lưu trữ 9 trường thông tin:

| Tên cột        | Kiểu dữ liệu    | Ý nghĩa                                                         |
| :--------------- | :----------------- | :---------------------------------------------------------------- |
| `article_id`   | `NVARCHAR(50)`   | **Khóa chính (Primary Key)** — Mã định danh bài báo |
| `title`        | `NVARCHAR(1000)` | Tiêu đề bài viết                                             |
| `description`  | `NVARCHAR(MAX)`  | Đoạn tóm tắt / Sa-pô                                         |
| `content`      | `NVARCHAR(MAX)`  | Toàn bộ nội dung văn bản (Full text)                         |
| `author`       | `NVARCHAR(255)`  | Tên phóng viên / Nguồn bài viết                             |
| `published_at` | `NVARCHAR(255)`  | Thời gian xuất bản (dạng chuỗi nguyên bản)                 |
| `category`     | `NVARCHAR(100)`  | Chuyên mục chính (Kinh doanh, Thế giới, Sức khỏe...)       |
| `subcategory`  | `NVARCHAR(100)`  | Chuyên mục phụ                                                 |
| `url`          | `NVARCHAR(1000)` | Đường dẫn bài viết gốc                                     |
| `created_at`   | `DATETIME`       | Thời gian hệ thống nạp bài vào CSDL                         |

---

## 3. Báo cáo thống kê mô tả dữ liệu

Toàn bộ dữ liệu được truy vấn trực tiếp từ SQL Server và trực quan hóa thành một bảng điều khiển với 4 biểu đồ:

1. **Biểu đồ 1: Phân bố số lượng bài theo chuyên mục (Bar Chart)**
2. **Biểu đồ 2: Hình thái phân bố độ dài bài báo (Histogram)**
3. **Biểu đồ 3: Tỷ lệ nguồn tác giả (Donut Chart)**
4. **Biểu đồ 4: Phân bố theo 24 khung giờ xuất bản (Bar Chart)**

---

## 4. Hướng dẫn cài đặt môi trường

### 4.1. Cài đặt Python & Thư viện

1. Cài đặt **Python 3.11 hoặc 3.12** (Lưu ý tích chọn `Add python.exe to PATH`).
2. Cài đặt toàn bộ thư viện cần thiết bằng 1 câu lệnh duy nhất:
   ```powershell
   pip install requests beautifulsoup4 lxml pandas pyodbc matplotlib
   ```

### 4.2. Cài đặt Microsoft SQL Server & SSMS

1. Cài đặt **SQL Server Express** (Instance mặc định: `.\SQLEXPRESS`) và **SSMS**.
2. Khởi tạo Database: Mở file `SQL importer/SQLschema.sql` trong SSMS và nhấn `F5` (hoặc để script tự tạo khi chạy).

---

## 5. Hướng dẫn vận hành hệ thống

Mở Terminal tại thư mục gốc `ADY201m Final` và thực thi lần lượt 3 lệnh:

```powershell
# Bước 1: Thu thập dữ liệu báo chí mới nhất
python "Web crawler\Webcrawler.py"

# Bước 2: Nạp dữ liệu vào Microsoft SQL Server
python "SQL importer\SQLimporter.py"

# Bước 3: Xuất thống kê mô tả và vẽ biểu đồ Dashboard
python "EDA + charts\Charts.py"
```
