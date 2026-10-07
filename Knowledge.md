# MASTER KNOWLEDGE BASE: KHOA HỌC DỮ LIỆU, PYTHON & CƠ SỞ DỮ LIỆU QUAN HỆ

> Tài liệu tri thức hợp nhất dành cho AI Agents, gồm 3 chuyên đề: ADY201m (Applied Data Science), PFP191 (Python for Everybody), DBI202 (Database Systems).
> Chỉ chứa lý thuyết, khái niệm, quy tắc và nguyên lý; không chứa mã mẫu.

## Mục lục
- Phần I: Khoa học dữ liệu & phương pháp luận (ADY201m)
- Phần II: Lập trình Python & OOP (PFP191)
- Phần III: Hệ thống cơ sở dữ liệu & thiết kế CSDL quan hệ (DBI202)
- Phần IV: Bản đồ tích hợp tri thức & nguyên tắc vận hành

---

# PHẦN I: KHOA HỌC DỮ LIỆU & PHƯƠNG PHÁP LUẬN (ADY201m)

## 1.1. Introduction to Data Science (Phần 1)

### Khái niệm & bản chất
- **Lịch sử tên gọi:** "Data Science" xuất hiện từ thập niên 1980-1990 khi các giáo sư thống kê tìm tên gọi phản ánh đúng bản chất hiện đại của ngành.
- **Process, not an Event:** Khoa học dữ liệu là quy trình liên tục dùng dữ liệu để thấu hiểu thế giới, không phải sự kiện đơn lẻ.
- **Giao thoa 3 lĩnh vực:**
  - Computer Science / IT: lập trình, cấu trúc dữ liệu, hệ thống phần mềm.
  - Math & Statistics: mô hình toán, xác suất, thống kê suy luận.
  - Domain / Business Knowledge: tri thức chuyên ngành, ngữ cảnh kinh doanh.
  - Giao điểm: Machine Learning (CS + Math), Traditional Research (Math + Domain), Software Development (CS + Domain).
- **Mục tiêu cốt lõi:** Làm lộ các insight ẩn và xu hướng sau dữ liệu thô, biến dữ liệu thành câu chuyện (storytelling) giúp tổ chức ra quyết định chiến lược.

### Bối cảnh bùng nổ
- Dữ liệu khổng lồ, thuật toán tiên tiến phát triển mạnh.
- Thuật toán mã nguồn mở miễn phí; lưu trữ và điện toán đám mây ngày càng rẻ.
- Chưa bao giờ có thời điểm thuận lợi hơn cho nhà khoa học dữ liệu.

### Nền tảng & 4 bước tổng quát
- **Nguồn dữ liệu đa dạng:** log files, email, mạng xã hội, dữ liệu bán hàng, hồ sơ bệnh nhân, dữ liệu thể thao, cảm biến, camera an ninh.
- **Vai trò với tổ chức:** thấu hiểu môi trường hoạt động; phân tích vấn đề hiện hữu; phát hiện cơ hội kinh doanh ẩn.
- **4 bước tổng quát:**
  1. (Quan trọng nhất) Đặt câu hỏi tò mò để làm rõ nhu cầu nghiệp vụ.
  2. Xác định dữ liệu cần và nguồn thu thập (có cấu trúc và phi cấu trúc).
  3. Dùng nhiều mô hình phân tích để tìm mẫu (patterns).
  4. Dùng trực quan hóa để truyền tải kết quả và đề xuất hành động cho stakeholders.

### Lời khuyên cho nhà khoa học dữ liệu mới
- **3 phẩm chất cốt lõi:**
  - Curious (tò mò): bắt buộc số 1.
  - Argumentative (hay tranh luận): đưa ra giả thuyết ban đầu rồi học từ dữ liệu để điều chỉnh.
  - Judgmental (biết phán đoán): có nhận định ban đầu để biết bắt đầu từ đâu.
- **Thái độ:** sẵn sàng thừa nhận giả thuyết sai ("Tôi từng nghĩ X, nhưng dữ liệu cho thấy Y").
- **Kỹ năng bắt buộc:** thành thạo ít nhất một nền tảng phân tích; khả năng kể chuyện từ dữ liệu; hiểu sâu một lĩnh vực cụ thể (y tế, giáo dục, tài chính...) làm lợi thế cạnh tranh.

## 1.2. Introduction to Data Science (Phần 2) - Case Studies

1. **Toronto Transit Commission (TTC):** Có 500,000 khiếu nại (dữ liệu phi cấu trúc như email/fax và có cấu trúc như thời gian, loại, người xử lý) nhưng không giải thích được các ngày tăng đột biến. Một chuyên viên bước xuống xe bus trúng vũng nước và đặt giả thuyết về thời tiết. Kết hợp dữ liệu Environment Canada cho thấy 10 ngày khiếu nại cao nhất trùng với thời tiết xấu bất ngờ (mưa rào bất chợt, nhiệt độ giảm sâu, tuyết giông). Bài học: tò mò và tình cờ (serendipity) dẫn đến phát hiện; không đổi được thời tiết nhưng giúp lãnh đạo hiểu bản chất vấn đề.
2. **Uber - Surge Pricing:** Dùng dữ liệu thời gian thực về tài xế khả dụng và nhu cầu khách; tăng giá giờ cao điểm để thu hút tài xế đến khu đông khách, phân bổ đúng số lượng, đúng nơi, đúng lúc.
3. **Streetcar Operations:** Dùng dữ liệu cảm biến/định vị (probe data) và khiếu nại để tìm điểm nghẽn giờ cao điểm. Số giờ lãng phí trung bình hàng tháng của người đi làm giảm từ 4.75 giờ (2010) xuống 3.0 giờ.
4. **Dự báo tảo độc ở hồ nước ngọt (Cyanobacterial Blooms):** Dùng thuyền robot, phao cảm biến, drone camera thu dữ liệu vật lý, hóa học, sinh học; xây mô hình dự báo thời điểm và vị trí bùng phát để bảo vệ nguồn nước và du lịch sinh thái.

## 1.3. Big Data & Nền tảng phân tích

### Định nghĩa & mô hình 5 V
- **Big Data (Ernst & Young):** tập dữ liệu động, quy mô lớn, đa dạng, tạo ra từ con người, công cụ và máy móc; cần công nghệ đổi mới, có khả năng mở rộng để thu thập, lưu trữ, xử lý, phân tích nhằm mang lại tri thức kinh doanh thời gian thực.
- **5 V:**
  1. Velocity (tốc độ): tốc độ dữ liệu phát sinh (ví dụ hàng trăm giờ video tải lên YouTube mỗi phút).
  2. Volume (dung lượng): quy mô khổng lồ (ví dụ thiết bị di động/IoT tạo khoảng 2.5 quintillion bytes mỗi ngày).
  3. Variety (đa dạng): văn bản, hình ảnh, âm thanh, y tế, cảm biến IoT.
  4. Veracity (độ tin cậy): chính xác và nguồn gốc; khoảng 80% dữ liệu hiện nay là phi cấu trúc nên cần phân loại và làm sạch.
  5. Value (giá trị): giá trị kinh doanh thực tế trích xuất được.

### Chuyển đổi số (Digital Transformation)
- Thay đổi tổ chức và văn hóa doanh nghiệp do Data Science và Big Data thúc đẩy.
- Ví dụ: Netflix (từ cho thuê DVD qua bưu điện sang xem phim trực tuyến); Houston Rockets (camera trên cao phân tích đường chuyền và vị trí ném rổ hiệu quả nhất); Lufthansa (phân tích dữ liệu hành khách để cá nhân hóa dịch vụ).

### Hệ sinh thái Hadoop
- Apache Hadoop: khung phần mềm mã nguồn mở cho tính toán phân tán trên cụm máy mở rộng đến hàng nghìn máy.
- Chịu lỗi ở tầng ứng dụng (Application Layer Fault-tolerance) thay vì dựa vào phần cứng đắt tiền.

### Data Analysis vs Data Mining
- **Data Analysis (5 giai đoạn):** Identify, Collect, Clean, Analyze, Interpret.
- **Data Mining (4 giai đoạn):** Data Gathering, Data Preparation, Mining the Data, Data Analysis & Interpretation (tạo mô hình thúc đẩy quyết định kinh doanh).

## 1.4. AI, Machine Learning & Deep Learning

- **AI (John McCarthy):** ngành khoa học và kỹ thuật chế tạo máy tính thông minh, đặc biệt là chương trình máy tính thông minh.
- **Ứng dụng AI phổ biến:** Speech Recognition (ASR, dựa trên NLP); Customer Service (trợ lý ảo); Computer Vision; Recommendation Engines; Automated Stock Trading (giao dịch tần suất cao không cần con người).
- **Machine Learning:** nhánh của AI dùng dữ liệu và thuật toán thống kê để bắt chước cách con người học, cải thiện độ chính xác theo thời gian.
- **Deep Learning:** tập con của ML, dùng mạng nơ-ron nhân tạo từ 3 lớp trở lên (có lớp ẩn) mô phỏng não bộ.

| Tiêu chí | Machine Learning | Deep Learning |
| :--- | :--- | :--- |
| Dữ liệu | Hoạt động tốt với dữ liệu vừa và nhỏ | Cần tập dữ liệu cực lớn |
| Độ chính xác | Khá tốt, chạm giới hạn khi dữ liệu tăng | Rất cao khi đủ dữ liệu |
| Thời gian huấn luyện | Ngắn | Dài (vài ngày đến vài tuần) |
| Phần cứng | CPU thông thường | Cần GPU / TPU |
| Tinh chỉnh | Hạn chế | Nhiều cách phức tạp |
| Loại thuật toán | Supervised, Unsupervised, Reinforcement | CNN, RNN |

## 2. Phương pháp luận Data Science (10 giai đoạn)

Chu trình: Business Understanding → Analytic Approach → Data Requirements → Data Collection → Data Understanding → Data Preparation → Modeling → Evaluation → Deployment → Feedback (và quay lại Business Understanding thành vòng lặp khép kín).

### 2.1. Giai đoạn 1: Business Understanding
- Bước khởi đầu bắt buộc; làm rõ mục tiêu (Goal) và mục tiêu cụ thể (Objectives) để xác định đúng loại dữ liệu.
- Thảo luận với stakeholders để đặt câu hỏi nghiên cứu rõ ràng.
- **Case study CHF (suy tim - Congestive Heart Failure):** Công ty bảo hiểm y tế Mỹ đối mặt nguy cơ bị cắt ngân sách hỗ trợ cho bệnh nhân tái nhập viện (theo tài liệu: 30% tái nhập viện trong 1 năm, 50% trong 5 năm). Yêu cầu kinh doanh: (1) dự đoán tái nhập viện CHF có/không; (2) dự đoán mức rủi ro; (3) hiểu chuỗi sự kiện dẫn đến nguy cơ; (4) dễ giải thích và áp dụng cho bác sĩ.

### 2.2. Giai đoạn 2: Analytic Approach
- **Phân loại câu hỏi và phương pháp:**
  - Descriptive: trạng thái hiện tại.
  - Diagnostic / Statistical: chuyện gì đã xảy ra và vì sao.
  - Predictive: điều gì sẽ xảy ra tiếp theo (xu hướng, xác suất).
  - Prescriptive: giải pháp tối ưu.
  - Classification: câu hỏi có/không.
  - Clustering / Association: tìm nhóm hành vi, mẫu hình.
- **Chọn cho CHF:** Decision Tree Classification, vì kết quả trực quan, minh bạch, giúp bác sĩ hiểu điều kiện gây rủi ro cao để can thiệp kịp thời.

### 2.3. Giai đoạn 3: Data Requirements
- Ví dụ nấu mỳ Ý (Spaghetti Analogy): dữ liệu là nguyên liệu; cần xác định đúng nguyên liệu, cách tìm, làm sạch, chế biến.
- **Yêu cầu cho CHF:** chọn nhóm (cohort) bệnh nhân nội trú trong khu vực phục vụ, có chẩn đoán chính CHF trong 1 năm liên tục và có bảo hiểm liên tục ít nhất 6 tháng trước đó. Cấu trúc: 1 dòng = 1 bệnh nhân; các cột là biến lịch sử lâm sàng (chẩn đoán, xét nghiệm, đơn thuốc, lịch sử nhập viện); mỗi bệnh nhân có thể có hàng nghìn bản ghi thô.

### 2.4. Giai đoạn 4: Data Collection
- Nguồn: nhân khẩu học, hồ sơ lâm sàng, bảo hiểm, chi phí điều trị, dược phẩm.
- **Dữ liệu thiếu:** có thể hoãn thu thập phần chưa sẵn sàng (ví dụ drug data chưa tích hợp) và vẫn xây mô hình thử nghiệm; mô hình CHF vẫn đạt kết quả tốt khi chưa có dữ liệu thuốc.
- Hành động kỹ thuật: trích xuất từ nhiều nguồn, hợp nhất, loại bỏ dữ liệu dư thừa, tự động hóa truy vấn CSDL.

### 2.5. Giai đoạn 5: Data Understanding
- Câu hỏi trung tâm: dữ liệu thu thập có đại diện đúng cho bài toán không?
- **Univariate statistics:** Mean, Median, Min, Max, Standard Deviation cho từng biến.
- **Pairwise correlations:** hai biến tương quan cực cao là dư thừa, chỉ giữ một.
- **Histograms:** xem phân bố, phát hiện outliers và missing values để lên kế hoạch xử lý.

### 2.6. Giai đoạn 6: Data Preparation
- Chiếm 70%-90% thời gian dự án (tự động hóa CSDL có thể giảm còn khoảng 50%).
- Công việc chính:
  1. Cleaning: xử lý missing values, bỏ giá trị không hợp lệ, xóa bản ghi trùng.
  2. Transformation: đưa dữ liệu về dạng dễ làm việc.
  3. Feature Engineering: dùng domain knowledge tạo biến mới giúp thuật toán học tốt hơn.
  4. Xử lý văn bản: tách từ, mã hóa văn bản thành ma trận số.

### 2.7. Giai đoạn 7: Modeling
- Tương tự "nếm thử nước sốt" để biết cần chỉnh thêm gì.
- Dùng Training Set (dữ liệu lịch sử đã biết kết quả) để huấn luyện và hiệu chỉnh tham số.
- Thử nhiều thuật toán để xác định biến quan trọng.

### 2.8. Giai đoạn 8: Evaluation
- Mục tiêu: kiểm tra chất lượng và đảm bảo mô hình trả lời đúng câu hỏi kinh doanh ban đầu trước khi triển khai.
- **Pha 1 - Diagnostic Measures:** kiểm tra mô hình hoạt động đúng thiết kế (Confusion Matrix, Precision/Recall cho Decision Tree).
- **Pha 2 - Statistical Significance Testing:** đảm bảo kết quả không do ngẫu nhiên.

### 2.9. Giai đoạn 9: Deployment
- Triển khai vào môi trường thử nghiệm hoặc nhóm người dùng giới hạn để củng cố độ tin cậy.
- Ví dụ: bản đồ rủi ro nhập viện do tiểu đường ở thanh thiếu niên; hệ thống đánh giá rủi ro bệnh nhân CHF thời gian thực cho bác sĩ.

### 2.10. Giai đoạn 10: Feedback
- Vòng lặp phản hồi từ người dùng cuối (bác sĩ, khách hàng, tư vấn viên) để tinh chỉnh mô hình; "càng biết nhiều càng muốn biết thêm".
- Giá trị mô hình phụ thuộc cập nhật dữ liệu mới và điều chỉnh thuật toán theo thời gian.
- Đánh giá hiệu quả: so sánh tỷ lệ tái nhập viện thực tế TRƯỚC và SAU khi áp dụng can thiệp.

## 3. Data Wrangling & Preprocessing thực hành (Pandas)

### 3.1. Nhập / xuất dữ liệu
- Pandas đọc/ghi các định dạng CSV, JSON, Excel, và truy vấn SQL (thông qua kết nối CSDL) vào DataFrame.
- Khi xuất dữ liệu nên bỏ cột chỉ mục (index) nếu không cần.

### 3.2. Xử lý giá trị khuyết thiếu
- **Dấu hiệu:** "?", "N/A", NaN, ô trống.
- **Chiến lược:**
  - Drop: xóa cột nếu thiếu quá nhiều; xóa dòng thiếu giá trị ở cột quan trọng (đặc biệt biến mục tiêu như price).
  - Replace: thay bằng Mean (biến số), Mode (biến phân loại), hoặc nội suy (interpolation).
  - Keep: giữ nguyên nếu mô hình hỗ trợ.

### 3.3. Chuẩn hóa định dạng
- Đưa các biểu diễn khác nhau của cùng một giá trị về một chuẩn (ví dụ "NY", "N.Y.", "New York" thành "New York").

### 3.4. Chuẩn hóa thang đo (Normalization)
Mục đích: đưa các biến có khoảng giá trị khác nhau (ví dụ Age 20-40, Income 20,000-500,000) về thang tương đương để không làm lệch mô hình.
1. **Simple Feature Scaling:** x_new = x_old / x_max
2. **Min-Max Normalization (về [0, 1]):** x_new = (x_old − x_min) / (x_max − x_min)
3. **Z-Score Standardization (Mean = 0, Std = 1):** x_new = (x_old − μ) / σ

### 3.5. Binning (nhóm khoảng)
- Chuyển biến số liên tục thành biến phân loại có thứ tự (ví dụ Price từ 5000 đến 45000 chia thành Low, Medium, High). Pandas dùng hàm `cut` cùng các mốc chia đều.

### 3.6. Mã hóa biến phân loại (Dummy Variables / One-Hot Encoding)
- Vấn đề: đa số mô hình thống kê/ML không nhận chuỗi.
- Giải pháp: tạo biến giả, gán 1 hoặc 0 cho mỗi danh mục (hàm `get_dummies`), sau đó nối vào DataFrame.

### 3.7. Lưu ý thực hành cho agent
- Kiểm tra missing bằng thống kê số ô thiếu theo cột (`isnull().sum()`).
- Cẩn thận khi áp công thức chuẩn hóa: dùng đúng cột cho cả tử số và mẫu số (lỗi thường gặp là tính Z-score của cột này nhưng gán sang cột khác).

---

# PHẦN II: LẬP TRÌNH PYTHON & HƯỚNG ĐỐI TƯỢNG (PFP191)

## 1. Giới thiệu lập trình & kiến trúc máy tính

### 1.1. Kiến trúc phần cứng
| Thành phần | Vai trò |
| :--- | :--- |
| CPU | Thực thi lệnh cực nhanh; không tự suy nghĩ, chỉ tuân thủ chính xác lệnh được giao. |
| Main Memory (RAM) | Lưu tạm dữ liệu và lệnh đang chạy; tốc độ cao nhưng mất khi tắt máy (volatile). |
| Secondary Memory | Lưu bền vững (SSD, HDD, USB); giữ dữ liệu khi mất điện (non-volatile). |
| I/O Devices | Giao tiếp người dùng - máy: bàn phím, chuột, màn hình, loa, mic. |

### 1.2. Compiler vs Interpreter
- **Compiler:** dịch toàn bộ mã nguồn sang mã máy một lần, tạo tệp thực thi trước khi chạy (C, C++).
- **Interpreter:** Python đọc, dịch và thực thi từng dòng từ trên xuống dưới theo thời gian thực.
- **Syntax Error:** vi phạm ngữ pháp thì trình thông dịch dừng ngay tại vị trí lỗi và báo lỗi.

### 1.3. Reserved Words
Không được dùng làm tên biến, hàm, lớp. 35 từ khóa: False, None, True, and, as, assert, async, await, break, class, continue, def, del, elif, else, except, finally, for, from, global, if, import, in, is, lambda, nonlocal, not, or, pass, raise, return, try, while, with, yield.

### 1.4. Luồng thực thi
1. Tuần tự: lệnh chạy nối tiếp từ trên xuống.
2. Điều kiện: chỉ chạy khối lệnh khi biểu thức logic đúng.
3. Lặp: lặp khối lệnh theo điều kiện dừng hoặc theo phần tử (for, while).

## 2. Biến, biểu thức & kiểu dữ liệu

### 2.1. Biến & hằng số
- **Hằng số:** giá trị cố định trong chương trình (123, 98.6, 'Hello').
- **Biến:** vùng nhớ có tên trong RAM, giá trị có thể thay đổi.
- **Quy tắc đặt tên:** bắt đầu bằng chữ cái hoặc gạch dưới (không bắt đầu bằng số); chỉ chứa chữ, số, gạch dưới; phân biệt hoa/thường; nên dùng tên gợi nhớ (mnemonic) như hours, rate, pay.

### 2.2. Toán tử số học
| Toán tử | Tên | Ý nghĩa |
| :---: | :--- | :--- |
| + | Cộng | Cộng số, nối chuỗi/danh sách |
| - | Trừ | Trừ số, đổi dấu |
| * | Nhân | Nhân số, lặp chuỗi/danh sách |
| / | Chia thực | Luôn trả về float |
| // | Chia nguyên | Lấy phần nguyên |
| % | Chia dư | Modulus |
| ** | Lũy thừa | Tính số mũ |

**Thứ tự ưu tiên:** (1) ngoặc đơn; (2) lũy thừa; (3) nhân, chia, chia nguyên, chia dư; (4) cộng, trừ; (5) cùng cấp thì tính từ trái sang phải.

### 2.3. Kiểu dữ liệu & chuyển kiểu
- Kiểu cơ bản: int, float, str (bọc trong nháy đơn hoặc kép), bool (True/False).
- `type()` trả về kiểu của đối tượng.
- `int()` (cắt phần thập phân hoặc chuyển chuỗi số), `float()`, `str()`.
- `input()` dừng chờ người dùng và **luôn trả về str**; muốn tính toán phải ép kiểu bằng `int()` hoặc `float()`.

## 3. Câu lệnh điều kiện & xử lý ngoại lệ

### 3.1. So sánh & thụt lề
- Toán tử so sánh: <, <=, ==, >=, >, != đều trả về bool.
- Thụt lề (chuẩn 4 khoảng trắng) xác định phạm vi khối lệnh; các lệnh cùng mức thụt lề thuộc cùng một khối.

### 3.2. Rẽ nhánh
- **if:** đúng thì chạy khối, sai thì bỏ qua.
- **if - else:** hai nhánh.
- **if - elif - else:** kiểm tra từ trên xuống; gặp điều kiện đúng đầu tiên thì chạy khối đó và bỏ qua các nhánh sau; không điều kiện nào đúng thì chạy else (nếu có).

### 3.3. try - except
- Đặt đoạn lệnh có nguy cơ lỗi (chuyển chuỗi sang số, mở file không tồn tại, chia cho 0) vào try.
- Không lỗi: bỏ qua except. Có lỗi tại bất kỳ dòng nào trong try: nhảy ngay sang except, tránh crash.

## 4. Hàm

### 4.1. Khái niệm & Store & Reuse
- Hàm là khối lệnh có tên, đóng gói một nhiệm vụ.
- Bước 1: định nghĩa bằng `def` (khối lệnh chưa chạy). Bước 2: gọi hàm bằng tên kèm ngoặc đơn, gọi bao nhiêu lần tùy ý.

### 4.2. Tham số vs đối số
- **Parameter (tham số):** biến đại diện khai báo khi định nghĩa hàm, nhận dữ liệu đầu vào.
- **Argument (đối số):** giá trị thực truyền vào khi gọi hàm.

### 4.3. Giá trị trả về
- **Fruitful function:** dùng `return` gửi kết quả về nơi gọi; có thể gán biến hoặc dùng trong biểu thức.
- **Void function:** làm một hành động (như in) không có return có giá trị; mặc định trả về `None`.

## 5. Vòng lặp & thuật toán lặp

### 5.1. while (indefinite loop)
- Kiểm tra điều kiện trước mỗi lượt; đúng thì chạy, sai thì kết thúc.
- **Infinite loop:** điều kiện luôn đúng làm chương trình treo.
- `break`: thoát hẳn vòng lặp. `continue`: bỏ phần còn lại của lượt hiện tại, quay về kiểm tra điều kiện.

### 5.2. for (definite loop)
- Duyệt từng phần tử của tập hữu hạn (chuỗi, list, tuple, dictionary, `range()`); tự dừng khi hết phần tử.

### 5.3. Các mô hình lặp chuẩn
1. **Counting:** biến đếm khởi tạo 0, tăng 1 mỗi phần tử.
2. **Summing:** biến tích lũy khởi tạo 0, cộng giá trị từng phần tử.
3. **Averaging:** kết hợp đếm và tổng; sau vòng lặp lấy tổng chia số lượng.
4. **Filtering:** dùng if trong vòng lặp để chỉ xử lý phần tử thỏa tiêu chí.
5. **Max / Min:** khởi tạo biến cực trị bằng `None`; cập nhật ở lượt đầu (khi còn None) hoặc khi gặp phần tử lớn hơn/nhỏ hơn.
- **`is` / `is not`:** so sánh định danh bộ nhớ (hai biến có trỏ cùng một vùng nhớ); nên dùng khi so với `None` hoặc boolean.

## 6. Chuỗi ký tự (Strings)

### 6.1. Index & Slicing
- Chỉ số bắt đầu từ 0; chỉ số âm đếm ngược (-1 là ký tự cuối). `len()` trả về số ký tự.
- **Slicing [bắt đầu : kết thúc]:** lấy từ vị trí bắt đầu đến kết thúc − 1 (không gồm kết thúc); bỏ trống bắt đầu thì mặc định 0; bỏ trống kết thúc thì lấy đến hết chuỗi.
- **Immutable:** chuỗi không thể sửa trực tiếp ký tự qua chỉ số; muốn đổi phải tạo chuỗi mới.

### 6.2. Phương thức phổ biến
- `.lower()`, `.upper()`: chuyển hoa/thường (trả chuỗi mới).
- `.strip()`, `.lstrip()`, `.rstrip()`: cắt khoảng trắng hai đầu / trái / phải.
- `.find(sub)`: vị trí xuất hiện đầu tiên, `-1` nếu không có.
- `.replace(old, new)`: thay mọi chuỗi con old bằng new.
- `.startswith(prefix)`, `.endswith(suffix)`: kiểm tra đầu/cuối, trả bool.

## 7. Thao tác với file

### 7.1. File handle
- `open(filename, mode)` tạo kết nối giữa chương trình và tệp trên đĩa.
  - Chế độ `'r'` (mặc định): đọc; lỗi nếu tệp không tồn tại.
  - Chế độ `'w'`: ghi; tệp tồn tại thì xóa sạch nội dung cũ; chưa có thì tạo mới.
- File handle không chứa toàn bộ nội dung mà là "cửa sổ" truy xuất từng dòng.

### 7.2. Đọc & xử lý nội dung
- **Đọc từng dòng bằng for:** tối ưu bộ nhớ vì không nạp cả tệp lớn vào RAM.
- **Ký tự `\n`:** mỗi dòng kết thúc bằng ký tự xuống dòng; dùng `.rstrip()` để tránh dòng trống thừa khi in.
- **`.read()`:** đọc cả tệp thành một chuỗi; chỉ nên dùng với tệp nhỏ và vừa.

## 8. Danh sách (Lists)

### 8.1. Đặc điểm
- Tập hợp có thứ tự trong ngoặc vuông, phân cách bằng dấu phẩy.
- **Mutable:** sửa, thêm, xóa phần tử trực tiếp qua chỉ số mà không tạo list mới (khác chuỗi).
- Có thể chứa nhiều kiểu dữ liệu khác nhau, kể cả list lồng nhau.

### 8.2. Thao tác
- `.append(x)`: thêm vào cuối. `.sort()`: sắp xếp tại chỗ (thay đổi list gốc).
- `in` / `not in`: kiểm tra tồn tại.
- Hàm tích hợp: `len()`, `max()`, `min()`, `sum()`.

### 8.3. Chuỗi và list
- `.split(delimiter)`: tách chuỗi thành list các chuỗi con (mặc định theo khoảng trắng); công cụ hàng đầu để phân tích văn bản.
- `.join(list)`: nối list chuỗi thành một chuỗi với ký tự phân cách chỉ định.

## 9. Từ điển (Dictionaries)

### 9.1. Cặp khóa - giá trị
- Cấu trúc ánh xạ (associative array) trong ngoặc nhọn, gồm các cặp Key - Value.
- Truy xuất, thêm, cập nhật qua Key tự định nghĩa, không dùng chỉ số 0, 1, 2.
- **Key:** phải bất biến (chuỗi, số, tuple), không trùng trong cùng dictionary. **Value:** kiểu bất kỳ, được trùng.

### 9.2. `.get()` & đếm tần suất
- `.get(key, default)`: trả giá trị của key nếu có; nếu chưa có trả về default mà không gây `KeyError`.
- **Thuật toán đếm tần suất:** duyệt dữ liệu, với mỗi phần tử lấy giá trị hiện tại bằng get với mặc định 0 rồi cộng 1 (lần đầu gặp thành 1).

### 9.3. Duyệt dữ liệu
- `.keys()`: tập các Key. `.values()`: tập các Value. `.items()`: tập các cặp (Key, Value) dạng tuple, cho phép for với hai biến lặp.

## 10. Tuples

### 10.1. So sánh List vs Tuple
| Tiêu chí | List | Tuple |
| :--- | :--- | :--- |
| Cú pháp | Ngoặc vuông | Ngoặc đơn |
| Tính biến đổi | Mutable | Immutable |
| Phương thức | Phong phú (append, sort, pop, extend...) | Rất hạn chế (count, index) |
| Tốc độ | Chậm hơn (quản lý bộ nhớ động) | Nhanh hơn (kích thước cố định) |
| Bộ nhớ | Tốn hơn | Tiết kiệm hơn |
| Mục đích | Dữ liệu thay đổi thường xuyên | Dữ liệu cố định; làm Key cho dictionary |

### 10.2. Ứng dụng
- **Tuple assignment:** gán đồng thời nhiều biến vế trái với các giá trị trong tuple vế phải.
- **So sánh & sắp xếp tuple:** so từng phần tử từ chỉ số 0; bằng nhau thì xét phần tử kế tiếp. Ứng dụng: sắp xếp dictionary theo Value bằng cách đảo cặp (Key, Value) thành (Value, Key).

## 11. OOP - Phần 1 (Basics)

### 11.1. Class & Object
- **Class:** bản thiết kế (blueprint) định nghĩa thuộc tính (dữ liệu) và phương thức (hành vi) chung.
- **Object / Instance:** bản thể cụ thể tạo từ class; một class tạo được nhiều object độc lập.
- **Vòng đời đối tượng:** khởi tạo, cấp phát bộ nhớ, thực thi phương thức, bị hủy khi không còn được tham chiếu.
- **`__init__()`:** constructor, tự chạy khi tạo object để thiết lập thuộc tính ban đầu.
- **`self`:** tham số đầu tiên của mọi phương thức, đại diện đối tượng hiện tại.

### 11.2. Encapsulation (Đóng gói)
- Gom dữ liệu và thao tác xử lý vào một class, che giấu chi tiết bên trong và bảo vệ dữ liệu khỏi truy cập/sửa đổi trái phép.
| Mức truy cập | Quy ước tên | Cơ chế |
| :--- | :--- | :--- |
| Public | Tên bình thường | Truy cập tự do từ ngoài |
| Protected | Bắt đầu bằng 1 gạch dưới | Quy ước dùng nội bộ class và class con |
| Private | Bắt đầu bằng 2 gạch dưới | Name Mangling, chỉ truy cập trong chính class |
- **Getters & Setters:** phương thức công khai kiểm soát đọc/ghi dữ liệu private, cho phép thêm logic kiểm tra hợp lệ trước khi gán.

### 11.3. Abstraction (Trừu tượng hóa)
- Tập trung vào đặc tính cốt lõi và giao diện bên ngoài, bỏ qua chi tiết cài đặt phức tạp.
- Trong Python: module `abc` (Abstract Base Classes) và decorator `@abstractmethod`; class con bắt buộc cài đặt lại giao diện.

## 12. OOP - Phần 2 (Advanced)

### 12.1. Inheritance & `super()`
- Class con tái sử dụng thuộc tính và phương thức của class cha, có thể mở rộng thêm.
- `super()` gọi phương thức của class cha (phổ biến nhất là gọi `__init__` của cha để tái sử dụng khởi tạo).

### 12.2. Method Overriding & Polymorphism
- **Overriding:** class con định nghĩa lại phương thức của cha (cùng tên và tham số) để tùy biến hành vi.
- **Polymorphism (đa hình):** các object thuộc class khác nhau phản hồi cùng một lời gọi phương thức theo cách riêng.

### 12.3. `@property`
- Decorator biến phương thức getter thành thuộc tính "ảo".
- Cho phép truy cập và gán giá trị bằng cú pháp thuộc tính thông thường nhưng vẫn kích hoạt getter/setter để kiểm tra logic đóng gói.

---

# PHẦN III: HỆ THỐNG CƠ SỞ DỮ LIỆU & THIẾT KẾ CSDL QUAN HỆ (DBI202)

## 1. Giới thiệu môn học & tổng quan hệ CSDL

### 1.1. Thông tin môn học
- Tên: Introduction to Database System (DBI202). Giáo trình: *First Course in Database Systems* - Jeffrey D. Ullman (Prentice Hall, 3rd Edition).
- **Cấu trúc đánh giá:** Progress Tests (ít nhất 2 bài) 10%; Lab (5 bài) 10%; Assignment (1 bài) 20%; Practical Exam 30%; Final Exam (lý thuyết, 60 phút) 30%.
- **Điều kiện hoàn thành:** mọi điểm thành phần > 0, Final Exam >= 4.0, điểm tổng kết >= 5.0.

### 1.2. Khái niệm cơ bản
- **Data vs Information:** dữ liệu là sự thật/giá trị thô; thông tin là dữ liệu đã xử lý, tổ chức để có ý nghĩa.
- **Database:** tập dữ liệu liên quan lưu lâu dài trên máy tính, quản lý bởi DBMS.
- **DBMS:** phần mềm hỗ trợ tạo lập, duy trì, khai thác CSDL điện tử.
- **Database System:** DBMS cùng dữ liệu được lưu, đôi khi gồm cả ứng dụng người dùng.

### 1.3. Lịch sử
1. **File Systems (1960s):** lưu trữ cơ bản, hạn chế về ngôn ngữ truy vấn, kiểm soát truy cập đồng thời, chịu lỗi.
2. **Hierarchical Model:** cấu trúc cây (IBM IMS).
3. **Network Model:** cấu trúc đồ thị (CODASYL, Charles Bachman), bản ghi có nhiều cha/con nhưng chưa có ngôn ngữ truy vấn cấp cao.
4. **Relational Model (1970s):** do Edgar F. "Ted" Codd đề xuất tại IBM; 1974 IBM phát triển SQL; 1979 Oracle v2 là RDBMS thương mại đầu tiên dùng SQL.
5. **Xu hướng hiện đại:** hệ thống nhỏ gọn (PC, mobile); hệ thống cực lớn (petabytes); tích hợp thông tin (Data Warehouse tập trung, hoặc Mediator/Middleware dịch truy vấn); NoSQL và NewSQL (MongoDB, Redis, ArangoDB).

### 1.4. Thành phần DBMS & ngôn ngữ
- **Nhóm người dùng:** DBA (quản trị truy cập, giám sát, cấp phát tài nguyên); Database Designers (định nghĩa nội dung, cấu trúc, ràng buộc, giao dịch); End Users (truy vấn, báo cáo, cập nhật).
- **DDL:** CREATE, ALTER, DROP; DDL Compiler thay đổi metadata (thông tin lược đồ).
- **DML:** SELECT, INSERT, UPDATE, DELETE; Query Compiler tối ưu thành Query Plan rồi giao Execution Engine thực thi.
- **Kiến trúc thành phần:** Query Compiler, Execution Engine, Transaction Manager, Buffer Manager, Storage Manager, Logging & Recovery, Concurrency Control (Lock Table), Index/File/Record Manager.

## 2. Mô hình quan hệ & đại số quan hệ

### 2.1. Data Model
Gồm 3 thành phần: cấu trúc dữ liệu (bảng, mảng, đồ thị), thao tác trên dữ liệu (truy vấn, biến đổi), ràng buộc trên dữ liệu. Các mô hình phổ biến: Relational Model và Semi-structured Data Model (ví dụ XML, cấu trúc lồng nhau dạng cây/đồ thị).

### 2.2. Khái niệm trong mô hình quan hệ
- **Relation** gồm: Schema (tên quan hệ, thuộc tính và domain, ví dụ Student(StudentID: string, Name: string, Registered: int)) và Instance (tập các tuple).
- **Cardinality:** số dòng (tuples). **Degree / Arity:** số cột (attributes).
- **Candidate Key:** tập thuộc tính tối thiểu xác định duy nhất mỗi tuple. **Primary Key:** candidate key được chọn làm định danh chính. **Foreign Key:** thuộc tính trỏ đến primary key của quan hệ khác, đảm bảo toàn vẹn tham chiếu.
- Còn có: Key / Non-key attribute, Multi-valued attribute (đa trị), Derived attribute (dẫn xuất).

### 2.3. Đại số quan hệ
Ngôn ngữ truy vấn thủ tục, các toán tử nhận quan hệ và tạo quan hệ mới.
1. **Set operations:** Union (∪): t thuộc R hoặc S; Intersection (∩): t thuộc cả hai; Difference (\): t thuộc R nhưng không thuộc S. Bắt buộc R và S **type compatible** (cùng số thuộc tính, cùng domain tương ứng).
2. **Selection σ_C(R):** lọc dòng thỏa điều kiện C. **Projection π_{A1..An}(R):** chọn cột và loại dòng trùng.
3. **Cartesian Product (R x S):** ghép mọi dòng R với mọi dòng S. **Theta Join (R ⋈_C S):** σ_C(R x S). **Natural Join (R ⋈ S):** nối trên thuộc tính chung có giá trị bằng nhau và bỏ cột trùng.
4. **Rename ρ_{S(A1..An)}(R):** đổi tên quan hệ hoặc thuộc tính.
- **Expression Tree:** SQL được Parser dịch thành biểu thức đại số quan hệ; Query Optimizer dùng cây biểu thức để tạo Query Execution Plan tối ưu.

## 3. Lý thuyết thiết kế CSDL quan hệ & chuẩn hóa

### 3.1. Phụ thuộc hàm (FD)
- **X → Y:** nếu hai tuple bất kỳ thống nhất trên X thì phải thống nhất trên Y.
- **Key:** K xác định hàm mọi thuộc tính khác và không có tập con nào cũng là key. **Superkey:** tập chứa một key.

**Tiên đề Armstrong:**
- Reflexivity: nếu Y ⊆ X thì X → Y.
- Augmentation: nếu X → Y thì XZ → YZ.
- Transitivity: nếu X → Y và Y → Z thì X → Z.
- Luật suy diễn bổ sung: Union (X → Y và X → Z thì X → YZ); Decomposition (X → YZ thì X → Y và X → Z); Pseudotransitivity (X → Y và WY → Z thì WX → Z).

**Bao đóng X+ & Minimal Basis:**
- X+ là tập mọi thuộc tính A sao cho X → A suy ra được từ tập FD. Thuật toán: bắt đầu từ X, liên tục thêm C nếu tồn tại B1..Bm → C với mọi Bi đã thuộc tập.
- **Minimal Basis:** tập FD tương đương thỏa: vế phải đơn (singleton), không xóa được FD nào, không xóa được thuộc tính nào ở vế trái.

### 3.2. Anomalies & Decomposition
- **3 bất thường:** Redundancy (dư thừa, lặp thông tin); Update Anomaly (sửa một dòng, quên dòng khác gây mất đồng nhất); Deletion Anomaly (xóa dòng làm mất thông tin quan trọng khác).
- **Decomposition:** tách R thành S và T. Yêu cầu: **Lossless Join** (khôi phục đúng R = S ⋈ T) và **Dependency Preservation** (giữ các FD sau khi tách).

### 3.3. Các dạng chuẩn
- **1NF:** mọi domain chỉ chứa giá trị nguyên tố (atomic), không tập hợp hay nhóm lặp.
- **2NF:** đạt 1NF và mọi thuộc tính không khóa phụ thuộc hàm đầy đủ vào khóa chính (không phụ thuộc một phần của khóa phức hợp).
- **3NF:** đạt 2NF và không có phụ thuộc bắc cầu giữa thuộc tính không khóa. Định nghĩa tổng quát: với mọi FD phi hiển nhiên X → A, hoặc X là superkey, hoặc A là thuộc tính khóa (prime attribute).
- **BCNF:** với mọi FD phi hiển nhiên X → A, X bắt buộc là superkey.
- **So sánh:** BCNF loại bỏ hoàn toàn dư thừa do FD nhưng có thể mất Dependency Preservation; 3NF cho phép dư thừa nhẹ nhưng luôn đảm bảo đồng thời Lossless Join và Dependency Preservation.

## 4. Mô hình CSDL cấp cao: ERD & UML

### 4.1. Quy trình thiết kế
1. Requirements Analysis (thu thập nhu cầu).
2. Conceptual Design (sơ đồ ERD cấp cao).
3. Logical Design (chuyển ERD sang lược đồ quan hệ).
4. Schema Refinement (chuẩn hóa).
5. Physical Design & Security Design (index, phân bố đĩa, bảo mật).
- **Kiến trúc 3 mức (Three-Schema):** External Level (external views) ↔ Conceptual Level (conceptual schema) ↔ Internal Level (internal schema / CSDL lưu trữ).

### 4.2. ERD
- **Entity / Entity Set:** đối tượng phân biệt được / tập các thực thể cùng loại.
- **Thuộc tính:** Key (gạch chân), Composite (gồm nhiều thành phần), Multi-valued (nét đôi), Derived (nét đứt).
- **Relationship:** liên kết giữa hai hay nhiều thực thể; multiplicity 1-1, 1-N, N-M; có thể có descriptive attributes.
- **Weak Entity Set:** không đủ thuộc tính để làm khóa chính, phụ thuộc Supporting Entity Set qua Supporting Relationship (nét đôi).
- **Subclass (ISA Hierarchy):** phân cấp kế thừa lớp cha - lớp con.

### 4.3. Quy tắc chuyển ERD / UML sang lược đồ quan hệ
1. **Strong Entity Set:** mỗi tập thành một bảng, thuộc tính thành cột.
2. **Composite Attribute:** phẳng hóa thành các cột thành phần.
3. **Multi-valued Attribute:** tạo bảng riêng gồm primary key của thực thể gốc + cột giá trị đa trị.
4. **Quan hệ 1-1 / 1-N:** đưa primary key bên 1 sang làm foreign key bên N.
5. **Quan hệ N-M:** tạo bảng liên kết chứa primary key của cả hai thực thể + thuộc tính của quan hệ.
6. **Weak Entity Set:** bảng gồm thuộc tính của thực thể yếu + primary key của thực thể hỗ trợ làm foreign key.
7. **Subclass:**
   - Phương pháp ER: bảng cho lớp cha và bảng cho từng lớp con chứa thuộc tính riêng + PK lớp cha.
   - Phương pháp OO: bảng hoàn chỉnh cho từng nhánh cây.
   - Phương pháp Null: một bảng duy nhất chứa mọi thuộc tính, điền NULL cho thuộc tính không có.

### 4.4. UML trong CSDL
- **UML Class:** tên lớp, thuộc tính (state), phương thức (behavior).
- **Association:** thay cho relationship của ER, thể hiện bản số bằng 0..*, 0..1, 1..1.
- **Association Class:** lớp hiệp hội chứa thuộc tính của mối quan hệ.
- **Aggregation & Composition:** quan hệ gộp và cấu thành (thường chuyển thành liên kết 1-N với ràng buộc toàn vẹn).

---

# PHẦN IV: BẢN ĐỒ TÍCH HỢP TRI THỨC & NGUYÊN TẮC VẬN HÀNH

## 1. Chu trình dữ liệu end-to-end
1. **Lưu trữ & quản trị (DBI202):** thiết kế ERD/UML, chuẩn hóa BCNF/3NF để tránh dư thừa và bất thường; quản trị bằng RDBMS (PostgreSQL, MySQL, SQL Server) với toàn vẹn ACID.
2. **Trích xuất & điều phối (PFP191):** kết nối CSDL qua thư viện (SQLAlchemy, psycopg2, pyodbc) với thiết kế OOP; xử lý file CSV/JSON/XML; quản lý lỗi bằng try - except; tổ chức dữ liệu bằng dict, list, tuple và hàm module hóa.
3. **Tiền xử lý & wrangling (ADY201m + Pandas):** điền/loại missing values; chuẩn hóa thang đo, binning, one-hot encoding; thống kê mô tả (univariate, correlations, histograms).
4. **Huấn luyện, đánh giá, kể chuyện (ADY201m methodology):** chọn analytic approach (classification, regression, clustering); đánh giá bằng diagnostic measures và statistical significance; triển khai, thiết lập feedback loop, trực quan hóa kết quả kinh doanh.

## 2. Đối chiếu khái niệm giữa các tầng công nghệ
| Thao tác | Đại số quan hệ | SQL | Pandas | Python thuần |
| :--- | :--- | :--- | :--- | :--- |
| Lọc dòng | Selection σ | WHERE | Lọc theo điều kiện boolean | Vòng lặp/duyệt kèm if (Filtering) |
| Chọn cột | Projection π | Danh sách cột trong SELECT | Chọn tập cột | Dựng dict mới chỉ với các key cần |
| Sắp xếp | Toán tử sắp xếp τ | ORDER BY | sort_values | sorted với key |
| Loại trùng | Loại trùng δ | DISTINCT | drop_duplicates | Dùng dict/set theo key |
| Gom nhóm & tính toán | Toán tử gom nhóm γ | GROUP BY kèm hàm gộp | groupby | Vòng lặp với get(key, 0) + 1 |
| Kết nối bảng | Join ⋈ | JOIN ... ON | merge | Hai vòng lặp lồng kiểm tra khóa chung |
| Hợp hai tập | Union ∪ | UNION | concat rồi drop_duplicates | Chuyển sang set rồi hợp |
| Đổi tên | Rename ρ | AS | rename | Đổi key trong dict |

## 3. Ma trận lựa chọn công cụ
| Tiêu chí | RDBMS / SQL | Python thuần / OOP | Pandas / NumPy |
| :--- | :--- | :--- | :--- |
| Vị trí tối ưu | Tầng lưu trữ và ACID | Tầng điều phối ứng dụng (logic, I/O, OOP) | Tầng phân tích số học và ML pipeline |
| Quy mô dữ liệu | Hàng chục GB đến TB | Vừa và nhỏ (phụ thuộc RAM) | Dưới ngưỡng RAM (thường dưới 10-20 GB) |
| Điểm mạnh | Toàn vẹn quan hệ, indexing, song song hóa | OOP linh hoạt, xử lý văn bản, API | Thao tác ma trận, vector hóa |
| Xử lý missing | COALESCE, NULLIF, IS NOT NULL | Kiểm tra None bằng if | fillna, dropna, interpolate |
| Feature engineering | Giới hạn ở phép toán cột cơ bản | Viết class/hàm tùy biến phức tạp | cut, get_dummies, apply |

## 4. Nguyên tắc vận hành cho AI Agents & Data Practitioners
1. **Push Down to DB:** thực hiện lọc thô (WHERE), cắt cột và gom nhóm ban đầu ngay tại DBMS trước khi kéo dữ liệu vào Python/Pandas để tiết kiệm mạng và RAM.
2. **Defensive Data Prep:** luôn xác thực kiểu dữ liệu (dtypes), kiểm tra missing values và outliers trước khi đưa vào thuật toán ML.
3. **Data-to-Decision Loop:** mỗi số liệu và biểu đồ phải phục vụ trực tiếp câu hỏi kinh doanh ban đầu và giải thích minh bạch được cho stakeholders.

---
*Tài liệu hợp nhất từ ADY201m, PFP191 và DBI202; nội dung trùng lặp giữa các file nguồn đã được gộp thành một bản duy nhất, loại bỏ mã mẫu và số tham chiếu trích dẫn.*
