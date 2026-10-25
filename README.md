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
   bóc tách 9 trường)                vào SQL Server )             xuất 5 ảnh PNG)
         │                                 │                               │
         ▼                                 ▼                               ▼
vnexpress_data.json              dbo.VnExpress_Articles          bieu_do_1..5_*.png
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
  2. Truy cập vào từng liên kết bài viết (nghỉ `CRAWL_DELAY` = 1.0s giữa các request), kiểm tra `is_article_page()` trước khi bóc tách: `og:type` phải là `article` (nếu trang có khai báo) và phải có thẻ `h1`. Trang video/clip/album (`og:type = website`, không có `h1`) bị loại ngay, không đưa vào dữ liệu.
  3. Bóc tách 9 trường dữ liệu (`article_id`, `title`, `description`, `content`, `author`, `published_at`, `category`, `subcategory`, `url`) bằng `BeautifulSoup`, làm sạch ngay trong lúc bóc:
     - Cắt tỉa khoảng trắng thừa (`.strip()`) và loại bỏ hoàn toàn các đoạn văn rỗng.
     - `extract_paragraphs()` thử nhiều selector dự phòng (`.fck_detail p.Normal` → `.fck_detail p` → ...) và chọn selector đầu tiên cho **từ ≥2 đoạn có chữ**, vì selector hẹp đôi khi chỉ bắt được dòng byline (trang trắc nghiệm); nếu không selector nào đủ thì dùng danh sách dự phòng.
     - Tách chữ ký tác giả in đậm (`<strong>`) ở đoạn cuối ra khỏi `content` để lưu vào cột `author`; bỏ qua `<strong>` rỗng nên không bị mất tên tác giả khi trang kết thúc bằng `<p><strong></strong></p>`.
     - `normalize_datetime()` đọc được cả chuỗi tiếng Việt (`"Thứ bảy, 17/10/2026, 23:37 (GMT+7)"` → bóc ngày `dd/mm/yyyy` + giờ `HH:mm`, bỏ dấu phẩy/GMT) và chuỗi ISO của `meta pubdate` (`2026-10-24T18:00`), ghép về `YYYY-MM-DD HH:MM:SS`; không parse được ngày thì để `null`.
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

* **Mục tiêu:** Truy vấn dữ liệu trực tiếp từ SQL Server, tính toán các chỉ số thống kê mô tả và xuất ra 5 biểu đồ (2 biểu đồ phân bố một biến + 3 biểu đồ quan hệ/cơ cấu), mỗi biểu đồ 1 file PNG riêng.
* **Luồng hoạt động:**
  1. Mở kết nối tới SQL Server, dùng lệnh SQL `SELECT ... FROM dbo.VnExpress_Articles` để tải toàn bộ các bản ghi đã lưu vào DataFrame của `pandas`.
  2. Tiền xử lý đặc trưng cho EDA:
     - Tính toán độ dài số từ của bài viết (`word_count`) từ trường `content` và độ dài mô tả (`desc_wc`) từ trường `description`.
     - Lấy khung giờ xuất bản (0h - 23h) trực tiếp từ cột `DATETIME` `published_at` bằng `pandas .dt.hour` (không còn parse chuỗi tiếng Việt mong manh như trước).
     - Chuẩn hóa nguồn bài viết thành biến phân loại nhị phân: `"Tác giả cụ thể"` vs `"Chung (VnExpress)"`.
  3. In các chỉ số thống kê mô tả ra terminal: tổng số bài, số bài có nội dung/mô tả rỗng, số bài thiếu `published_at`, count/mean/std/min/max cho `word_count` và `hour`, cùng tần số chuyên mục.
  4. Dùng `matplotlib` dựng 5 biểu đồ và lưu thành 5 file PNG riêng trong `EDA + charts/`: top 10 chuyên mục con (bar), số bài lũy kế theo giờ (line/ECDF), tương quan mô tả - nội dung (scatter), cơ cấu tác giả theo chuyên mục (stacked bar 100%) và heatmap chuyên mục × khung giờ (`bieu_do_1_*.png` ... `bieu_do_5_*.png`), tô màu theo 20 bậc rời (thấp = xanh biển, giữa = xanh lá, cao = đỏ).

---

## 2. Thư viện Python sử dụng

| Thư viện                   | Chức năng trong dự án                                                                |
| :--------------------------- | :--------------------------------------------------------------------------------------- |
| `requests`                 | Gửi HTTP Request tải RSS Feed và trang bài viết từ VnExpress.                      |
| `beautifulsoup4` (`bs4`) | Phân tích cú pháp HTML/XML, bóc tách 9 trường dữ liệu từ từng bài báo.     |
| `lxml`                     | Parser XML tốc độ cao, được BeautifulSoup dùng làm backend khi đọc RSS Feed.   |
| `pandas`                   | Cấu trúc dữ liệu dạng DataFrame, tính toán thống kê mô tả và xuất file CSV. |
| `pyodbc`                   | Kết nối và thực thi câu lệnh SQL tới Microsoft SQL Server qua ODBC Driver.        |
| `matplotlib`               | Vẽ 5 biểu đồ trực quan hóa và xuất ra 5 file ảnh PNG.                           |

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

Toàn bộ dữ liệu được truy vấn trực tiếp từ SQL Server (`dbo.VnExpress_Articles`) và trực quan hóa thành **5 biểu đồ**, mỗi biểu đồ xuất ra 1 file PNG riêng trong `EDA + charts/`. Hai biểu đồ đầu mô tả phân bố của một biến (chuyên mục con, khung giờ); ba biểu đồ sau mô tả quan hệ giữa hai biến hoặc cơ cấu bên trong từng nhóm. Số liệu dưới đây ứng với lần cào đầy đủ ngày 25/10/2026 (sau khi sửa crawler): **40 bài**, snapshot 24/10 15:12–21:55.

| # | Biểu đồ | Loại | Trường dữ liệu | Câu hỏi thống kê |
| :-: | :--- | :--- | :--- | :--- |
| 1 | Top 10 chuyên mục con | Bar chart | `subcategory` | Chuyên mục con nào xuất hiện nhiều nhất? |
| 2 | Số bài xuất bản lũy kế theo giờ | Line chart (ECDF) | `published_at` → `hour` | Bao nhiêu % bài đã đăng trước giờ t? Trung vị và P80 là mấy giờ? |
| 3 | Độ dài mô tả và độ dài nội dung | Scatter plot | `description`, `content` | Hai độ dài có tương quan không, mạnh hay yếu? |
| 4 | Cơ cấu nguồn tác giả theo chuyên mục | Stacked bar 100% | `category`, `author` | Trong từng chuyên mục, tỷ lệ byline chung là bao nhiêu? |
| 5 | Chuyên mục × khung giờ xuất bản | Heatmap | `category`, `published_at` | Chuyên mục nào đăng nhiều vào giờ nào? |

### 4.1. Biểu đồ 1 — Top 10 chuyên mục con (Bar Chart)

* **Dạng:** cột ngang, hiển thị số bài kèm % trên tổng số bài có nhãn chuyên mục con.
* **Trường dữ liệu:** `subcategory`.
* **Ý nghĩa thống kê:** xếp hạng tần số của biến phân loại cấp 2, tức tìm mode và mức độ tập trung của nhãn. Biến này có **cardinality cao** (21 nhãn khác nhau trên 30 bài có nhãn) nên chỉ vẽ top 10 để tránh biểu đồ rối; phần đuôi dài cho thấy dữ liệu phân mảnh mạnh.
* **Kết quả hiện tại:** tính trên 30/40 bài có `subcategory` (10 bài ghi "Không có" không vẽ): Các bệnh 3 bài (10,0%); bảy nhãn cùng 2 bài (6,7% mỗi nhãn) gồm Tin tức, Doanh nghiệp, Bắc Mỹ, Ngoại hạng Anh, Xe điện, Bóng đá, Nhạc; các nhãn còn lại chỉ 1 bài.
* **Lưu ý:** một phần tư số bài (10/40) thiếu chuyên mục con, nên bảng xếp hạng chỉ phản ánh nhóm có nhãn. Với đỉnh chỉ 3 bài, không nên suy ra mức độ phổ biến ngoài trang báo.

### 4.2. Biểu đồ 2 — Số bài xuất bản lũy kế theo giờ (Line Chart / ECDF)

* **Dạng:** đường bậc thang (step) của tần số lũy kế theo %, kèm vùng tô và hai đường phân vị.
* **Trường dữ liệu:** `published_at` → `hour`; 40/40 bài có timestamp.
* **Ý nghĩa thống kê:** đây là **hàm phân bố tích lũy thực nghiệm (ECDF)**: tại giờ t, tung độ là P(giờ đăng ≤ t). Cách vẽ này cho phép đọc **phân vị trực tiếp trên đồ thị** (giao với mốc 50% ra trung vị, 80% ra P80) mà không phụ thuộc việc chọn độ rộng bin như histogram; độ dốc của đường cho biết tốc độ tích lũy bài trong từng khoảng giờ.
* **Kết quả hiện tại:** trung vị 18h (50% bài đăng trước 18h), P80 = 20h, đạt 100% lúc 21h. Theo giờ: 15h (6 bài), 16h (4), 17h (7), 18h (7), 19h (6), 20h (7), 21h (3).
* **Lưu ý:** dữ liệu chỉ phủ 15:12–21:55 ngày 24/10. Đoạn phẳng 0h–15h và sau 21h là do phạm vi snapshot, không phải nhịp đăng thực tế; muốn kết luận về khung giờ phải có nhiều ngày.

### 4.3. Biểu đồ 3 — Độ dài mô tả và độ dài nội dung (Scatter Plot)

* **Dạng:** scatter plot hai trục định lượng, có đường hồi quy tuyến tính.
* **Trường dữ liệu:** `description` → `desc_wc`, `content` → `word_count`.
* **Ý nghĩa thống kê:** mô tả **phân bố đồng thời** của hai biến định lượng, cho thấy hướng, độ mạnh và dạng của mối liên hệ, đồng thời phát hiện outlier và cụm điểm. **Pearson r** đo quan hệ tuyến tính; **Spearman ρ** đo quan hệ đơn điệu và ít bị outlier chi phối. Hệ số xác định r² ≈ 0,006 nghĩa là độ dài mô tả gần như không giải thích được phương sai độ dài nội dung.
* **Kết quả hiện tại:** cả 40 bài đều có đủ `description` và `content`: Pearson r = -0,076; Spearman ρ = -0,094 → gần như không có tương quan. Vì quality gate đã loại bài rỗng nội dung, Pearson tính trên 40 bài và tính gộp toàn mẫu cho cùng một giá trị (không còn các điểm (0 từ) kéo lệch hệ số như lần cào trước).
* **Lưu ý:** không thể dùng độ dài sa-pô để dự báo độ dài bài. Tương quan không phải nhân quả; nếu sau này mẫu có bài khuyết dữ liệu, phải nêu rõ mẫu tính vì việc gộp điểm rỗng làm thay đổi dấu và độ lớn của hệ số.

### 4.4. Biểu đồ 4 — Cơ cấu nguồn tác giả trong từng chuyên mục (Stacked Bar 100%)

* **Dạng:** cột ngang xếp chồng chuẩn hóa 100%, sắp xếp theo tỷ lệ byline chung tăng dần; nhãn mục kèm n.
* **Trường dữ liệu:** `category` × `author_type`.
* **Ý nghĩa thống kê:** biểu diễn **phân bố có điều kiện** P(author_type | category). Chuẩn hóa về 100% giúp so sánh *cơ cấu* giữa các chuyên mục có quy mô khác nhau, nhưng đồng thời **xóa mất quy mô** — số lượng tuyệt đối đã ghi kèm trong nhãn `(n)` ở trục tung.
* **Kết quả hiện tại:** toàn mẫu 1/40 bài (2,5%) dùng byline chung. Theo chuyên mục: Kinh doanh 33% (1/3); 14 chuyên mục còn lại đều 0%.
* **Lưu ý:** sau khi crawler loại trang video/clip, không còn bài nào rơi vào nhóm "Khác", nên hiện tượng "Khác = 100% byline chung" của lần cào trước đã biến mất — đúng như dự đoán đó là lỗi thiếu metadata chứ không phải đặc điểm của chuyên mục. Các mục có n = 1–3 cho tỷ lệ 0%/33% rất bấp bênh.

### 4.5. Biểu đồ 5 — Số bài theo chuyên mục và khung giờ xuất bản (Heatmap)

* **Dạng:** heatmap 4 chuyên mục × 7 khung giờ (15h–21h), ô ghi số bài; màu rời từ xám (0) → xanh (ít) → đỏ (nhiều).
* **Trường dữ liệu:** `category` × `hour` (từ `published_at`).
* **Ý nghĩa thống kê:** biểu diễn **bảng tần số chéo (contingency table)** của hai biến định tính. Đây là biểu đồ duy nhất cho thấy tương tác giữa hai chiều cùng lúc: cụm ô đậm = chuyên mục tập trung đăng trong một khung giờ; ô xám = không có bài trong mẫu. Có thể đọc thêm tổng hàng (quy mô chuyên mục) và tổng cột (quy mô khung giờ) từ chính biểu đồ.
* **Kết quả hiện tại:** 4 chuyên mục chính có ≥4 bài (40 bài có timestamp, 0 bài thiếu): Thế giới (6), Sức khỏe (4), Giải trí (4), Thể thao (4). Điểm nổi bật: Thế giới 2 bài lúc 15h; Sức khỏe 2 bài lúc 16h; Thể thao 2 bài lúc 18h; Giải trí rải đều 17h/18h/20h/21h (mỗi giờ 1 bài).
* **Lưu ý:** ngưỡng ≥4 bài được chọn tự động theo cỡ mẫu (6% của 40, tối thiểu 4) để tránh ma trận quá thưa. Ô 0 chỉ có nghĩa "không có bài trong mẫu", không phải "chuyên mục đó không bao giờ đăng giờ đó"; không nên chạy chi-square trên ma trận này.

### 4.6. Giới hạn chung khi đọc kết quả

Toàn bộ 5 biểu đồ là **thống kê mô tả trên một mẫu 40 bài thuộc một RSS snapshot ngày 24/10/2026** (cào ngày 25/10), không phải điều tra toàn bộ hoạt động của VnExpress. Các giới hạn cần nêu khi bảo vệ:

* Trong 45 liên kết RSS, crawler giữ 40 bài và loại 5: 4 trang video/clip (`og:type = website`) và 1 trang điểm tin không có tiêu đề/nội dung (5136453). Toàn bộ 40 bài đã lưu đều có `title`, `content`, `description` và `published_at`.
* 10/40 bài (25%) không có `subcategory` (ghi "Không có"); 1/40 bài dùng byline mặc định `"VnExpress"`.
* Quy mô mỗi chuyên mục rất nhỏ (lớn nhất 6 bài, nhiều mục 1–2 bài), nên mọi tỷ lệ % và so sánh giữa nhóm chỉ mang tính mô tả.
* Dữ liệu chỉ phủ 15:12–21:55 của một ngày; mọi kết luận về "khung giờ vàng" hay nhịp xuất bản cần thêm nhiều ngày cào.
* Không có kiểm định suy luận (t-test, chi-square, hồi quy suy diễn); các hệ số tương quan chỉ dùng để mô tả mức liên hệ trong mẫu.

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

# Bước 3: Xuất thống kê mô tả và vẽ 5 biểu đồ PNG
python "EDA + charts\Charts.py"
```
