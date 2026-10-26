# Báo cáo dự án nhóm 6 (Mô tả dữ liệu từ báo VNExpress)

Thành viên nhóm và phân công:

**Đinh Trung Hiếu**: phụ trách EDA

**Phạm Hùng Dương**: phụ trách web crawler

**Nguyễn Hữu Hùng**: phụ trách SQL

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
vnexpress_data.json              dbo.VnExpress_Articles          bieu_do_1_chuyen_muc.png
vnexpress_data.csv               (Database: ADY201m)             bieu_do_2_phan_bo_gio.png
                                                                 bieu_do_3_tac_gia.png
                                                                 bieu_do_4_nhiet_do_chuyen_muc_gio.png
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
  2. Truy cập vào từng liên kết bài viết (nghỉ `CRAWL_DELAY` = 1.0s giữa các request), kiểm tra `is_article_page()` trước khi bóc tách: `og:type` phải là `article` (nếu trang có khai báo) và phải có thẻ `h1`. Trang video/clip/album (`og:type = website`, không có `h1`) bị loại ngay, không đưa vào dữ liệu.
  3. Bóc tách 9 trường dữ liệu (`article_id`, `title`, `description`, `content`, `author`, `published_at`, `category`, `subcategory`, `url`) bằng `BeautifulSoup`, làm sạch ngay trong lúc bóc:
     - Cắt tỉa khoảng trắng thừa (`.strip()`) và loại bỏ hoàn toàn các đoạn văn rỗng.
     - `extract_paragraphs()` thử nhiều selector dự phòng (`.fck_detail p.Normal` → `.fck_detail p` → ...) và chọn selector đầu tiên cho **từ ≥2 đoạn có chữ**, vì selector hẹp đôi khi chỉ bắt được dòng byline (trang trắc nghiệm); nếu không selector nào đủ thì dùng danh sách dự phòng.
     - Tách chữ ký tác giả in đậm (`<strong>`) ở đoạn cuối ra khỏi `content` để lưu vào cột `author`; bỏ qua `<strong>` rỗng nên không bị mất tên tác giả khi trang kết thúc bằng `<p><strong></strong></p>`.
     - `normalize_datetime()` đọc được cả chuỗi tiếng Việt (`"Thứ bảy, 17/10/2026, 23:37 (GMT+7)"` → bóc ngày `dd/mm/yyyy` + giờ `HH:mm`, bỏ dấu phẩy/GMT) và chuỗi ISO của `meta pubdate` (`2026-10-24T18:00`), ghép về `YYYY-MM-DD HH:MM:SS`; không parse được ngày thì để `null`.
     - Tách `category`/`subcategory` từ breadcrumb; mục đầu là icon home không có chữ nên lấy thuộc tính `title` thay thế, sau đó bỏ các mục rỗng — tránh trường hợp `category` bị chuỗi rỗng.
     - `description` lấy từ `p.description`; bài không có sao-pô thì lấy `meta[name=description]`, sau đó `og:description`.
     - **Quality gate:** bài thiếu `title` hoặc thiếu `content` bị loại, không ghi vào JSON/CSV/CSDL.
     - Xử lý giá trị khuyết thiếu: Gán mặc định `"Không có"` cho tiểu mục, `"Khác"` cho chuyên mục, và `"VnExpress"` cho bài không đề tên tác giả.
  4. Đóng gói và lưu đồng thời ra 2 định dạng file tại thư mục `Web crawler/`:
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

* **Mục tiêu:** Truy vấn dữ liệu trực tiếp từ SQL Server, tính toán các chỉ số thống kê mô tả và xuất ra 4 biểu đồ (3 biểu đồ phân bố một biến + 1 biểu đồ quan hệ giữa hai biến), mỗi biểu đồ 1 file PNG riêng.
* **Luồng hoạt động:**
  1. Mở kết nối tới SQL Server, dùng lệnh SQL `SELECT ... FROM dbo.VnExpress_Articles` để tải toàn bộ các bản ghi đã lưu vào DataFrame của `pandas`.
  2. Tiền xử lý đặc trưng cho EDA:
     - Tính toán độ dài số từ của bài viết (`word_count`) từ trường `content` và độ dài mô tả (`desc_wc`) từ trường `description`; hai chỉ số này dùng cho phần thống kê mô tả ở terminal, không còn là trục của biểu đồ.
     - Lấy khung giờ xuất bản (0h - 23h) trực tiếp từ cột `DATETIME` `published_at` bằng `pandas .dt.hour` (không còn parse chuỗi tiếng Việt mong manh như trước).
  3. In các chỉ số thống kê mô tả ra terminal: tổng số bài, số bài có nội dung/mô tả rỗng, số bài thiếu `published_at`, count/mean/std/min/max cho `word_count` và `hour`, cùng tần số chuyên mục.
  4. Dùng `matplotlib` dựng 4 biểu đồ và lưu thành 4 file PNG riêng trong `EDA + charts/`: số bài theo toàn bộ chuyên mục (bar ngang), số bài theo 24 khung giờ (histogram, màu động theo tần số), cơ cấu tác giả (pie hai lát: VnExpress và các tác giả khác) và heatmap chuyên mục × khung giờ (`bieu_do_1_chuyen_muc.png` ... `bieu_do_4_nhiet_do_chuyen_muc_gio.png`). Biểu đồ 1, 2 và 4 tô màu theo 10 bậc rời (thấp = xanh biển, giữa = xanh lá, cao = đỏ); biểu đồ 3 dùng cặp xanh/xám để phân biệt hai nhóm.

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

Dữ liệu được truy vấn trực tiếp từ SQL Server (`dbo.VnExpress_Articles`) và trực quan hóa thành 4 biểu đồ, mỗi biểu đồ xuất ra một file PNG riêng trong `EDA + charts/`. Ba biểu đồ đầu mô tả phân bố của một biến (chuyên mục, khung giờ, tác giả); biểu đồ 4 mô tả quan hệ giữa hai biến (chuyên mục × khung giờ).

| # | Biểu đồ | Loại | Trường dữ liệu | Câu hỏi thống kê |
| :-: | :--- | :--- | :--- | :--- |
| 1 | Số bài theo chuyên mục | Bar chart ngang | `category` | Mỗi chuyên mục có bao nhiêu bài, cơ cấu ra sao? |
| 2 | Số bài xuất bản theo 24 khung giờ | Histogram (24 bin) | `published_at` → `hour` | Mỗi giờ có bao nhiêu bài, phân bố tập trung ở đâu? |
| 3 | Cơ cấu tác giả bài viết | Pie chart | `author` | Bao nhiêu % bài do byline mặc định VnExpress, bao nhiêu % do tác giả có tên? |
| 4 | Chuyên mục × khung giờ xuất bản | Heatmap | `category`, `published_at` | Chuyên mục nào đăng nhiều vào giờ nào? |

### 4.1. Biểu đồ 1 — Số bài theo chuyên mục (Bar Chart)

* **Dạng:** cột ngang, hiển thị toàn bộ chuyên mục có trong dữ liệu (không cắt top 10), sắp xếp tăng dần, mỗi cột ghi số bài kèm % trên tổng số bài; màu lấy theo 10 bậc rời của thang giá trị.
* **Trường dữ liệu:** `category`.
* **Ý nghĩa thống kê:** đếm tần số của biến phân loại cấp 1, qua đó thấy cả nhóm dẫn đầu lẫn phần đuôi dài. Vẽ đủ nhãn giúp không bỏ sót chuyên mục nhỏ, đổi lại các cột ít bài khá mảnh.
* **Lưu ý:** quy mô mỗi chuyên mục trong một lần cào thường nhỏ, nên chênh lệch vài bài chưa nói lên thứ hạng ổn định. Biến `subcategory` phân mảnh nên không vẽ thành biểu đồ riêng.

### 4.2. Biểu đồ 2 — Số bài xuất bản theo 24 khung giờ (Histogram)

* **Dạng:** histogram 24 cột, mỗi cột là một khung giờ 0h–23h, chiều cao là số bài trong giờ đó; cột tô màu động theo tần số (10 bậc rời), đầu cột ghi số bài, trục x hiện 24 nhãn giờ 0h–23h.
* **Trường dữ liệu:** `published_at` → `hour`.
* **Ý nghĩa thống kê:** đếm tần số tuyệt đối của biến định lượng rời rạc `hour` với bin cố định 1 giờ, phủ đủ 24 bin. Histogram cho thấy trực tiếp quy mô từng giờ, giờ cao điểm và các khoảng trống mà không phải đọc chênh lệch giữa hai điểm như biểu đồ đường; đổi lại, bin 1 giờ làm mất khác biệt trong cùng giờ.
* **Lưu ý:** cột bằng 0 nghĩa là ngoài phạm vi mẫu, không phải "giờ đó không đăng bài"; số cột trống phụ thuộc khoảng thời gian mà RSS trả về trong lần cào. Bin rộng 1 giờ gộp mọi bài trong cùng giờ nên không thấy được khác biệt phút.

### 4.3. Biểu đồ 3 — Cơ cấu tác giả bài viết (Pie Chart)

* **Dạng:** pie chart hai lát: `VnExpress` (xanh) và Các tác giả khác (xám); nhãn ngoài chỉ ghi tên nhóm, tỷ lệ % ghi bên trong lát.
* **Trường dữ liệu:** `author` (crawler gán `"VnExpress"` cho bài không đề tên tác giả).
* **Ý nghĩa thống kê:** tách dữ liệu thành hai nhóm loại trừ nhau để trả lời một câu hỏi nhị phân: bao nhiêu phần bài do byline mặc định `VnExpress` và bao nhiêu do tác giả có tên. Pie chart phù hợp vì hai lát cộng lại đúng 100%.
* **Lưu ý:** `"VnExpress"` là byline mặc định, không phải một người viết thật, nên biểu đồ này phản ánh chất lượng dữ liệu (tỷ lệ bài thiếu byline) hơn là cơ cấu tác giả chi tiết. Nhóm "Các tác giả khác" gộp nhiều người, không thể so sánh ai viết nhiều hơn ai; muốn xem chi tiết phải quay lại bảng tần số `author`.

### 4.4. Biểu đồ 4 — Số bài theo chuyên mục và khung giờ xuất bản (Heatmap)

* **Dạng:** heatmap các chuyên mục đủ ngưỡng × 24 khung giờ (0h–23h), ô ghi số bài; màu rời từ xám (0) → xanh (ít) → đỏ (nhiều); vùng vẽ được thu nhỏ và căn giữa khung ảnh.
* **Trường dữ liệu:** `category` × `hour` (từ `published_at`).
* **Ý nghĩa thống kê:** biểu diễn bảng tần số chéo (contingency table) của hai biến định tính. Đây là biểu đồ cho thấy tương tác giữa hai chiều cùng lúc: cụm ô đậm = chuyên mục tập trung đăng trong một khung giờ; ô xám = không có bài trong mẫu. Có thể đọc thêm tổng hàng (quy mô chuyên mục) và tổng cột (quy mô khung giờ) từ chính biểu đồ.
* **Lưu ý:** ngưỡng ≥4 bài được chọn tự động theo cỡ mẫu (`max(4, 6% × n)`) để tránh ma trận thưa, nên các chuyên mục nhỏ không xuất hiện trên hình. Ô 0 chỉ có nghĩa "không có bài trong mẫu", không phải "chuyên mục đó không bao giờ đăng giờ đó"; không nên chạy chi-square trên ma trận này.

### 4.5. Giới hạn chung khi đọc kết quả

Toàn bộ 4 biểu đồ là thống kê mô tả trên dữ liệu của một lần cào RSS, không phải điều tra toàn bộ hoạt động của VnExpress. Các giới hạn cần nêu khi bảo vệ:

* Dữ liệu chỉ phủ khoảng thời gian mà RSS trả về trong lần cào; mọi kết luận về nhịp xuất bản cần thêm nhiều ngày thu thập.
* Một số bài không có `subcategory` (ghi "Không có") và các nhãn chuyên mục con phân bố mỏng, nên không dùng để phân tích sâu.
* Byline mặc định `"VnExpress"` là quy ước của crawler, không đại diện một người viết thật.
* Quy mô mỗi chuyên mục nhỏ, nên mọi tỷ lệ % và so sánh giữa nhóm chỉ mang tính mô tả.
* Không có kiểm định suy luận (t-test, chi-square, hồi quy); mọi tỷ lệ % chỉ mô tả mẫu hiện có.

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
