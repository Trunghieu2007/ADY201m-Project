# Báo cáo dự án nhóm 6 (Mô tả dữ liệu từ báo VnExpress)

Thành viên nhóm và phân công:

**Đinh Trung Hiếu**: phụ trách phân tích dữ liệu (EDA)

**Phạm Hùng Dương**: phụ trách web crawler

**Nguyễn Hữu Hùng**: phụ trách SQL

---

## 1. Kiến trúc hệ thống

Hệ thống gồm 3 bước:

![Sơ đồ 3 bước: Web crawler → SQL importer → EDA + charts](<Vietnamese%20Data%20Workflow%20Pipeline.png>)

### 1.1. Ý nghĩa thực tiễn của mô tả dữ liệu

**Ứng dụng theo lĩnh vực:**

- **A. Báo chí và truyền thông:** theo dõi nhịp độ xuất bản theo giờ và chuyên mục; phân tích độ dài và đặc điểm nội dung; so sánh cơ cấu tin tức giữa các chuyên mục; làm nền cho việc theo dõi truyền thông và lập báo cáo truyền thông.
- **B. Phân tích xã hội:** theo dõi biến động các chủ đề kinh tế, giáo dục, y tế, môi trường và chính sách qua cơ cấu chuyên mục; phát hiện chủ đề mới hoặc tăng tần suất bất thường khi có chuỗi dữ liệu nhiều đợt cào; đối chiếu các nhận định về nội dung báo chí với số liệu thay vì dựa vào cảm nhận.
- **C. Kinh doanh và thị trường:** theo dõi các nhóm chủ đề Kinh doanh, Bất động sản và Khoa học công nghệ, hỗ trợ nghiên cứu thị trường và theo dõi tin liên quan đến ngành hoặc thương hiệu. Các phát hiện chỉ nên dùng để xây dựng giả thuyết, không tự động coi là kết luận kinh doanh.
- **D. Y tế, khoa học và công nghệ:** theo dõi mức độ chú ý của truyền thông dành cho sức khỏe và công nghệ mới; so sánh chủ đề khoa học qua nhiều giai đoạn khi có thêm dữ liệu.
- **E. Giáo dục và nghiên cứu:** cung cấp bộ dữ liệu tiếng Việt có ghi rõ nguồn để thực hành thống kê mô tả, trực quan hóa, tái lập kết quả và mở rộng kho dữ liệu cho nghiên cứu tiếp theo.

*Lưu ý:* biểu đồ khung giờ phản ánh mẫu cào tại thời điểm chạy, không đại diện cho nhịp xuất bản trong ngày.

### 1.2. Thu thập và làm sạch dữ liệu tại nguồn (`Web crawler`)

* **Mục tiêu:** Thu thập bài mới từ nguồn tin RSS của VnExpress và làm sạch dữ liệu ngay khi bóc tách.
* **Luồng hoạt động:**
  1. Gửi yêu cầu HTTP tải danh sách bài viết mới từ nguồn tin RSS (`https://vnexpress.net/rss/tin-moi-nhat.rss`) bằng thư viện `requests` và bộ phân tích XML `lxml`. Các yêu cầu đi qua hàm `fetch()` có gọi `raise_for_status()` (bắt lỗi 4xx/5xx để không nạp trang rác) và đặt `encoding = "utf-8"`.
  2. Truy cập vào từng liên kết bài viết (nghỉ `CRAWL_DELAY` = 1.0s giữa các yêu cầu), kiểm tra `is_article_page()` trước khi bóc tách: `og:type` cần là `article` (nếu trang có khai báo) và trang cần có thẻ `h1`. Trang video/clip/album (`og:type = website`, không có `h1`) bị loại, không đưa vào dữ liệu.
  3. Bóc tách 9 trường dữ liệu (`article_id`, `title`, `description`, `content`, `author`, `published_at`, `category`, `subcategory`, `url`) bằng `BeautifulSoup`, làm sạch ngay trong lúc bóc:
     - Cắt khoảng trắng thừa (`.strip()`) và bỏ các đoạn văn rỗng.
     - `extract_paragraphs()` thử nhiều bộ chọn dự phòng (`.fck_detail p.Normal` → `.fck_detail p` → ...) và chọn bộ chọn đầu tiên cho từ 2 đoạn có chữ trở lên, vì bộ chọn hẹp đôi khi chỉ bắt được dòng tên tác giả (trang trắc nghiệm); nếu không bộ chọn nào đủ thì dùng danh sách dự phòng.
     - Tách chữ ký tác giả in đậm (`<strong>`) ở đoạn cuối ra khỏi `content` để lưu vào cột `author`; bỏ qua `<strong>` rỗng nên không bị mất tên tác giả khi trang kết thúc bằng `<p><strong></strong></p>`.
     - `normalize_datetime()` đọc được cả chuỗi tiếng Việt (`"Thứ bảy, 17/10/2026, 23:37 (GMT+7)"` → bóc ngày `dd/mm/yyyy` + giờ `HH:mm`, bỏ dấu phẩy/GMT) và chuỗi ISO của `meta pubdate` (`2026-10-24T18:00`), ghép về `YYYY-MM-DD HH:MM:SS`; không đọc được ngày thì để `null`.
     - Tách `category`/`subcategory` từ dải liên kết chuyên mục ở đầu trang; mục đầu là biểu tượng trang chủ không có chữ nên lấy thuộc tính `title` thay thế, sau đó bỏ các mục rỗng — tránh trường hợp `category` bị chuỗi rỗng.
     - `description` lấy từ `p.description`; bài không có sao-pô thì lấy `meta[name=description]`, sau đó `og:description`.
     - **Bộ lọc chất lượng:** bài thiếu `title` hoặc thiếu `content` bị loại, không ghi vào JSON/CSV/CSDL.
     - Xử lý giá trị khuyết thiếu: gán mặc định `"Không có"` cho tiểu mục, `"Khác"` cho chuyên mục, và `"VnExpress"` cho bài không đề tên tác giả.
  4. Đóng gói và lưu đồng thời ra 2 định dạng file tại thư mục `Web crawler/`:
     - `vnexpress_data.json`.
     - `vnexpress_data.csv`.

### 1.3. Lưu trữ và khử trùng lặp (`SQL importer`)

* **Mục tiêu:** Nạp dữ liệu từ file JSON vào Microsoft SQL Server, giữ tính toàn vẹn và tích lũy dữ liệu theo thời gian.
* **Luồng hoạt động:**
  1. Tìm và nạp file `vnexpress_data.json` từ thư mục `Web crawler/`.
  2. Kiểm tra database: mở kết nối tới `master`, truy vấn `sys.databases` xem `ADY201m` đã tồn tại chưa. Nếu chưa, in thông báo yêu cầu người dùng chạy `SQL importer/SQLschema.sql` và dừng.
  3. Kiểm tra bảng: nối trực tiếp `ADY201m`, kiểm tra `dbo.VnExpress_Articles` qua `OBJECT_ID`. Nếu bảng chưa có, in thông báo để chạy `SQLschema.sql` và dừng lại; mã nguồn không tự tạo bảng.
  4. Khử trùng lặp hai bước: trước hết loại `article_id` trùng ngay trong lô dữ liệu JSON (tránh vi phạm khóa chính), rồi đối chiếu với tập `article_id` đã có trong CSDL để chỉ giữ bài mới.
  5. Nạp theo lô bằng `executemany` với `fast_executemany = True`. Trường `published_at` được chuyển về kiểu `datetime` để ghi vào cột `DATETIME`. Nếu lệnh chèn hàng loạt lỗi, chương trình chuyển sang chèn từng dòng trong `try/except` để một dòng lỗi không làm hỏng cả lô, và in báo cáo số bài chèn được / thất bại.

### 1.4. Mô tả dữ liệu và trực quan hóa (`EDA + charts`)

* **Mục tiêu:** Truy vấn dữ liệu trực tiếp từ SQL Server, tính các chỉ số thống kê mô tả và xuất ra 4 biểu đồ (3 biểu đồ phân bố một biến + 1 biểu đồ quan hệ giữa hai biến), mỗi biểu đồ một file PNG riêng.
* **Luồng hoạt động:**
  1. Mở kết nối tới SQL Server, dùng lệnh SQL `SELECT ... FROM dbo.VnExpress_Articles` để tải các bản ghi đã lưu vào DataFrame của `pandas`.
  2. Chuẩn bị dữ liệu cho bước phân tích khám phá (EDA):
     - Tính độ dài bài viết (`word_count`) từ trường `content` và độ dài mô tả (`desc_wc`) từ trường `description`; hai chỉ số này dùng cho phần thống kê mô tả ở cửa sổ dòng lệnh, không dùng làm trục biểu đồ.
     - Lấy khung giờ xuất bản (0h - 23h) trực tiếp từ cột `DATETIME` `published_at` bằng `pandas .dt.hour`, không phải đọc chuỗi tiếng Việt như cách cũ.
  3. In các chỉ số thống kê mô tả ra cửa sổ dòng lệnh: tổng số bài, số bài có nội dung/mô tả rỗng, số bài thiếu `published_at`, số lượng/trung bình/độ lệch chuẩn/nhỏ nhất/lớn nhất cho `word_count` và `hour`, cùng tần số chuyên mục.
  4. Dùng `matplotlib` dựng 4 biểu đồ và lưu thành 4 file PNG riêng trong `EDA + charts/`: số bài theo từng chuyên mục (biểu đồ cột ngang), số bài theo 24 khung giờ (biểu đồ tần số, màu động theo tần số), cơ cấu tác giả (biểu đồ tròn hai phần: VnExpress và các tác giả khác) và bản đồ nhiệt chuyên mục × khung giờ (`bieu_do_1_chuyen_muc.png` ... `bieu_do_4_nhiet_do_chuyen_muc_gio.png`). Biểu đồ 1, 2 và 4 tô màu theo 20 bậc rời (thấp = xanh biển, giữa = xanh lá, cao = đỏ); biểu đồ 3 dùng cặp xanh/xám để phân biệt hai nhóm.

---

## 2. Thư viện Python sử dụng

| Thư viện                   | Chức năng trong dự án                                                                        |
| :--------------------------- | :----------------------------------------------------------------------------------------------- |
| `requests`                 | Gửi yêu cầu HTTP tải nguồn tin RSS và trang bài viết từ VnExpress.                      |
| `beautifulsoup4` (`bs4`) | Phân tích cú pháp HTML/XML, bóc tách 9 trường dữ liệu từ từng bài báo.             |
| `lxml`                     | Bộ phân tích XML, được BeautifulSoup dùng làm bộ xử lý nền khi đọc nguồn tin RSS. |
| `pandas`                   | Cung cấp cấu trúc DataFrame, tính thống kê mô tả và xuất file CSV.                     |
| `pyodbc`                   | Kết nối và thực thi câu lệnh SQL tới Microsoft SQL Server qua ODBC Driver.                |
| `matplotlib`               | Vẽ 4 biểu đồ và xuất ra 4 file ảnh PNG.                                                   |

---

## 3. Mô tả cấu trúc dữ liệu

Bảng **`dbo.VnExpress_Articles`** trên Microsoft SQL Server gồm 10 trường thông tin (9 trường bóc tách từ crawler + `created_at`):

| Tên cột        | Kiểu dữ liệu    | Ý nghĩa                                                                   |
| :--------------- | :----------------- | :-------------------------------------------------------------------------- |
| `article_id`   | `NVARCHAR(50)`   | Khóa chính — mã định danh bài báo                                   |
| `title`        | `NVARCHAR(1000)` | Tiêu đề bài viết                                                       |
| `description`  | `NVARCHAR(MAX)`  | Đoạn tóm tắt / sao-pô                                                  |
| `content`      | `NVARCHAR(MAX)`  | Toàn văn nội dung bài viết                                             |
| `author`       | `NVARCHAR(255)`  | Tên phóng viên / nguồn bài viết                                       |
| `published_at` | `DATETIME`       | Thời gian xuất bản (đã chuyển về kiểu datetime ở bước thu thập) |
| `category`     | `NVARCHAR(100)`  | Chuyên mục chính (Kinh doanh, Thế giới, Sức khỏe...)                 |
| `subcategory`  | `NVARCHAR(100)`  | Chuyên mục phụ                                                           |
| `url`          | `NVARCHAR(1000)` | Đường dẫn bài viết gốc                                               |
| `created_at`   | `DATETIME`       | Thời gian hệ thống nạp bài vào CSDL                                   |

---

## 4. Báo cáo thống kê mô tả dữ liệu

Dữ liệu được truy vấn trực tiếp từ SQL Server (`dbo.VnExpress_Articles`) và trực quan hóa thành 4 biểu đồ, mỗi biểu đồ xuất ra một file PNG riêng trong `EDA + charts/`. Ba biểu đồ đầu mô tả phân bố của một biến (chuyên mục, khung giờ, tác giả); biểu đồ 4 mô tả quan hệ giữa hai biến (chuyên mục × khung giờ).

![Bảng tóm tắt 4 biểu đồ EDA](<Vietnamese%20Data%20Table.png>)

### 4.1. Biểu đồ 1 — Số bài theo chuyên mục (biểu đồ cột ngang)

* **Dạng:** cột ngang, hiển thị các chuyên mục có trong dữ liệu (không chỉ lấy 10 chuyên mục đầu), sắp xếp tăng dần theo số bài, mỗi cột ghi số bài kèm % trên tổng số bài; cột tô màu theo 20 bậc rời của thang giá trị. Trục x được matplotlib chia mốc tự động theo độ lớn dữ liệu nên nhãn không bị chồng khi số bài tăng.
* **Trường dữ liệu:** `category`.
* **Ý nghĩa thống kê:** đếm tần số của biến phân loại cấp 1, qua đó thấy cả nhóm dẫn đầu lẫn phần đuôi dài. Vẽ đủ nhãn giúp không bỏ sót chuyên mục nhỏ, đổi lại các cột ít bài khá mảnh.
* **Cách đọc:** so sánh chiều dài cột để thấy quy mô từng chuyên mục; đọc nhãn số bài kèm % để biết tỷ trọng trên tổng số bài; màu chỉ là lớp phụ trợ thị giác, số liệu nằm ở độ dài cột và nhãn; chú ý phần đuôi dài — nhiều chuyên mục chỉ vài bài cho thấy mẫu phân tán.
* **Ứng dụng:** theo dõi truyền thông — dựng bức tranh cơ cấu tin tức của một trang báo trong một khoảng thời gian và theo dõi tỷ trọng từng chuyên mục qua nhiều đợt cào; biên tập và lập kế hoạch nội dung — nhận diện chuyên mục đăng nhiều, chuyên mục đăng ít để đối chiếu với mục tiêu; nghiên cứu xã hội — quan sát mức độ chú ý của báo chí dành cho từng lĩnh vực; kiểm tra chất lượng dữ liệu — một chuyên mục chiếm tỷ lệ bất thường có thể là dấu hiệu bước thu thập lấy sai nhóm chuyên mục hoặc nguồn tin RSS lệch chủ đề.
* **Lưu ý:** quy mô mỗi chuyên mục trong một lần cào thường nhỏ, nên chênh lệch vài bài chưa nói lên thứ hạng ổn định. Biến `subcategory` phân mảnh nên không vẽ thành biểu đồ riêng.

### 4.2. Biểu đồ 2 — Số bài xuất bản theo 24 khung giờ (biểu đồ tần số)

* **Dạng:** biểu đồ tần số 24 cột, mỗi cột là một khung giờ 0h–23h, chiều cao là số bài trong giờ đó; cột tô màu động theo tần số (20 bậc rời), đầu cột ghi số bài; trục x hiện đủ 24 nhãn giờ 0h–23h, trục y là số bài với mốc chia tự động; giờ không có bài vẫn giữ một cột trống.
* **Trường dữ liệu:** `published_at` → `hour`.
* **Ý nghĩa thống kê:** đếm tần số tuyệt đối của biến định lượng rời rạc `hour` với khoảng chia cố định 1 giờ, phủ 24 khoảng. Biểu đồ tần số cho thấy trực tiếp quy mô từng giờ, giờ cao điểm và các khoảng trống mà không phải đọc chênh lệch giữa hai điểm như biểu đồ đường; đổi lại, khoảng chia 1 giờ làm mất khác biệt trong cùng giờ.
* **Cách đọc:** so sánh chiều cao cột để biết giờ nào đăng nhiều, giờ nào vắng; nhìn các cột liền kề để thấy cụm cao điểm thay vì một giờ đơn lẻ; tổng chiều cao các cột bằng số bài có thời điểm xuất bản, dùng để kiểm tra biểu đồ khớp cỡ mẫu; cột bằng 0 trong phạm vi mẫu nghĩa là giờ đó không có bài mới, còn cột 0 ngoài phạm vi chỉ là do mẫu chưa phủ tới.
* **Ứng dụng:** chọn thời điểm đăng bài để tránh đè tin hoặc chọn giờ ít cạnh tranh; nhận diện cao điểm xuất bản để lập lịch trực và kiểm duyệt; so sánh hình dạng biểu đồ giữa các ngày hoặc các trang báo để thấy khác biệt về thói quen đăng tin; đánh giá độ phủ của một lần cào để không suy rộng ra cả ngày; lập lịch thu thập — chạy crawler vào hoặc ngay sau các giờ cao điểm.
* **Lưu ý:** cột bằng 0 nghĩa là ngoài phạm vi mẫu, không phải "giờ đó không đăng bài"; số cột trống phụ thuộc khoảng thời gian mà nguồn tin RSS trả về trong lần cào. Khoảng chia rộng 1 giờ gộp mọi bài trong cùng giờ nên không thấy được khác biệt phút.

### 4.3. Biểu đồ 3 — Cơ cấu tác giả bài viết (biểu đồ tròn)

* **Dạng:** biểu đồ tròn hai phần: `VnExpress` (xanh) và Các tác giả khác (xám); nhãn ngoài chỉ ghi tên nhóm, tỷ lệ % ghi bên trong mỗi phần.
* **Trường dữ liệu:** `author` (crawler gán `"VnExpress"` cho bài không đề tên tác giả).
* **Ý nghĩa thống kê:** tách dữ liệu thành hai nhóm loại trừ nhau để trả lời một câu hỏi nhị phân: bao nhiêu phần bài do tên tác giả mặc định `VnExpress` và bao nhiêu do tác giả có tên. Biểu đồ tròn phù hợp vì hai phần cộng lại đúng 100%.
* **Cách đọc:** so sánh hai phần — phần xanh càng lớn thì tỷ lệ bài không có tên tác giả càng cao; hai phần cộng lại 100%; không suy ra ai viết nhiều nhất từ biểu đồ này vì nhóm xám đã gộp nhiều người.
* **Ứng dụng:** kiểm tra chất lượng dữ liệu — đo trực tiếp tỷ lệ bài thiếu tên tác giả, nếu phần VnExpress tăng bất thường qua các đợt cào thì cần xem lại cách bóc tách tên tác giả; đánh giá độ tin cậy trước khi phân tích tác giả — cần biết bao nhiêu bài không xác định được người viết; theo dõi qua thời gian để phát hiện thay đổi cấu trúc trang; mô tả cấu trúc nguồn tin — phần lớn nội dung đến từ nhiều cây bút khác nhau hay chỉ một nhóm nhỏ.
* **Lưu ý:** `"VnExpress"` là tên tác giả mặc định, không phải một người viết thật, nên biểu đồ này phản ánh chất lượng dữ liệu (tỷ lệ bài thiếu tên tác giả) hơn là cơ cấu tác giả chi tiết. Nhóm "Các tác giả khác" gộp nhiều người, không thể so sánh ai viết nhiều hơn ai; muốn xem chi tiết cần quay lại bảng tần số `author`. Biểu đồ tròn chỉ so sánh tỷ trọng, không dùng để so sánh số bài tuyệt đối với biểu đồ khác.

### 4.4. Biểu đồ 4 — Số bài theo chuyên mục và khung giờ xuất bản (bản đồ nhiệt)

* **Dạng:** bản đồ nhiệt các chuyên mục đủ ngưỡng × 24 khung giờ (0h–23h); mỗi ô là số bài của chuyên mục trong giờ đó, ô có bài tô màu theo 20 bậc rời và ghi số trắng ở giữa, ô không có bài để xám nhạt và không ghi số; lưới trắng phân tách các ô, hình được kéo rộng để đủ chỗ cho 24 cột giờ và vùng vẽ được thu nhỏ, căn giữa khung ảnh.
* **Trường dữ liệu:** `category` × `hour` (từ `published_at`).
* **Ý nghĩa thống kê:** biểu diễn bảng tần số chéo của hai biến định tính. Đây là biểu đồ cho thấy tương tác giữa hai chiều cùng lúc: cụm ô đậm là chuyên mục tập trung đăng trong một khung giờ; ô xám là không có bài trong mẫu. Có thể đọc thêm tổng hàng (quy mô chuyên mục) và tổng cột (quy mô khung giờ) từ chính biểu đồ.
* **Cách đọc:** đọc theo hàng để biết một chuyên mục đăng rải đều hay dồn vào vài giờ; đọc theo cột để thấy giờ nào nhiều chuyên mục cùng đăng; ô đậm kèm số lớn là cụm tập trung, ô xám chỉ có nghĩa không có bài trong mẫu; tổng hàng xấp xỉ quy mô chuyên mục, tổng cột xấp xỉ quy mô khung giờ.
* **Ứng dụng:** lập lịch biên tập — biết chuyên mục nào đăng vào giờ nào để tránh trùng giờ hoặc dồn nguồn lực kiểm duyệt đúng cao điểm; tìm khung giờ đăng nhiều theo chuyên mục để chủ động đẩy tin cùng khung; phát hiện bất thường — một ô cao đột biến so với các ô cùng hàng là tín hiệu có sự kiện hoặc lỗi thu thập; quy hoạch nguồn lực theo mật độ bài; so sánh thói quen giờ đăng giữa nhiều đợt cào.
* **Lưu ý:** ngưỡng tối thiểu được chọn tự động theo cỡ mẫu (`max(4, 6% × n)`) và giới hạn tối đa 9 chuyên mục để tránh ma trận thưa, nên các chuyên mục nhỏ không xuất hiện trên hình. Ma trận vẫn thưa vì mỗi ô chỉ là một chuyên mục × một giờ; các cột trống thường do phạm vi mẫu chứ không phải chuyên mục không đăng giờ đó. Ô 0 chỉ có nghĩa "không có bài trong mẫu", không phải "chuyên mục đó không bao giờ đăng giờ đó"; không nên chạy kiểm định chi bình phương trên ma trận này.

### 4.6. Giới hạn chung khi đọc kết quả


- Một số bài không có `subcategory` (ghi "Không có") và các nhãn chuyên mục con phân bố mỏng, nên không dùng để phân tích sâu.



- Tên tác giả mặc định `"VnExpress"` là quy ước của crawler để gắn trường tác giả cho những bài không có tác giả cụ thể.


### 4.5. Quy ước màu dùng chung

* Bảng **20 màu rời, cách đều**: xanh biển `#1f78b4` → xanh ngọc → xanh lá → vàng → cam → đỏ `#e31a1c`.
* Hàm `mau_theo_gia_tri(values)` ánh xạ mỗi giá trị về một bậc theo công thức `chỉ số = round((v - min) / (max - min) × 19)`, nhờ vậy thang màu tự thích nghi với dữ liệu mới mà không phải sửa code.
* Bản đồ nhiệt dùng thêm `#f2f2f2` cho ô 0 (không có bài), phần còn lại lấy từ bảng 20 màu.
* Biểu đồ 3 dùng cặp màu cố định: xanh `#1f78b4` cho VnExpress, xám `#bdbdbd` cho nhóm còn lại, vì chỉ có 2 nhóm nên thang 20 bậc không còn ý nghĩa định lượng.
* Màu chỉ là lớp phụ trợ; mọi biểu đồ đều ghi số liệu trực tiếp nên vẫn đọc được khi in đen trắng.

---

## 5. Hướng dẫn cài đặt môi trường

### 5.1. Cài đặt Python và thư viện

1. Cài đặt **Python 3.11 hoặc 3.12** (nhớ tích chọn `Add python.exe to PATH`).
2. Cài các thư viện (phiên bản đã ghi trong `requirements.txt`) bằng một lệnh:
   ```powershell
   pip install -r requirements.txt
   ```

### 5.2. Cài đặt Microsoft SQL Server và SSMS

1. Cài đặt **SQL Server Express** (mặc định: `.\SQLEXPRESS`) và **SSMS**.
2. Trước khi nạp, cần khởi tạo cấu trúc database: mở file `SQL importer/SQLschema.sql` trong SSMS và nhấn `F5` để tạo database `ADY201m` và bảng `dbo.VnExpress_Articles`. `SQLimporter.py` không tự tạo database/bảng — nếu chưa có, chương trình in thông báo hướng dẫn chạy file này và dừng lại.
3. Nâng cấp từ phiên bản cũ: nếu bảng đã tồn tại với cột `published_at` kiểu `NVARCHAR` (dữ liệu lẫn nhiều định dạng), chạy `DROP TABLE dbo.VnExpress_Articles;` rồi chạy lại `SQLschema.sql` để cột `published_at` đúng kiểu `DATETIME`, sau đó chạy lại 3 bước.

---

## 6. Hướng dẫn vận hành hệ thống

Mở cửa sổ dòng lệnh tại thư mục gốc `ADY201m Final` và chạy lần lượt 3 lệnh:

```powershell
# Bước 1: Thu thập bài báo mới
python "Web crawler\Webcrawler.py"

# Bước 2: Nạp dữ liệu vào Microsoft SQL Server
python "SQL importer\SQLimporter.py"

# Bước 3: Xuất thống kê mô tả và vẽ 4 biểu đồ PNG
python "EDA + charts\Charts.py"
```
