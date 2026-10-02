# 🧠 KNOWLEDGE BASE: CHUYÊN ĐỀ TÀI LIỆU SLIDE PPTX MON ADY201m
> **Tài liệu tổng hợp chuyên sâu toàn bộ kiến thức từ 10 tệp bài giảng PPTX dành cho AI Agents & Data Science Practitioners.**

---

## 📌 MỤC LỤC TỔNG QUAN

1. [Chương 1.1: Introduction to Data Science (Phần 1)](#chuong-11-introduction-to-data-science-phan-1)
2. [Chương 1.2: Introduction to Data Science (Phần 2) - Bài toán & Case Studies](#chuong-12-introduction-to-data-science-phan-2---bai-toan--case-studies)
3. [Chương 1.3: Data Science Topic 1 - Big Data & Nền Tảng Phân Tích](#chuong-13-data-science-topic-1---big-data--nen-tang-phan-tich)
4. [Chương 1.4: Data Science Topic 2 - AI, Machine Learning & Deep Learning](#chuong-14-data-science-topic-2---ai-machine-learning--deep-learning)
5. [Chương 2.1: Data Science Methodology - From Problem to Analytic Approach](#chuong-21-data-science-methodology---from-problem-to-analytic-approach)
6. [Chương 2.2: Data Science Methodology - From Requirements to Data Collection](#chuong-22-data-science-methodology---from-requirements-to-data-collection)
7. [Chương 2.3: Data Science Methodology - From Understanding to Data Preparation](#chuong-23-data-science-methodology---from-understanding-to-data-preparation)
8. [Chương 2.4: Data Science Methodology - From Modeling to Evaluation](#chuong-24-data-science-methodology---from-modeling-to-evaluation)
9. [Chương 2.5: Data Science Methodology - From Deployment to Feedback](#chuong-25-data-science-methodology---from-deployment-to-feedback)
10. [Chương 2.6: Practical Data Science Steps in Python (Data Wrangling & Preprocessing)](#chuong-26-practical-data-science-steps-in-python-data-wrangling--preprocessing)

---

## 📘 CHƯƠNG 1.1: INTRODUCTION TO DATA SCIENCE (PHẦN 1)
*Nguồn: `1.1 Introduction to Data Science 1.pptx`*

### 1. Khái niệm & Bản chất Khoa học Dữ liệu (Defining Data Science)
+ **Lịch sử tên gọi:** Thuật ngữ "Data Science" bắt đầu xuất hiện và phổ biến từ thập niên 1980 - 1990 khi các giáo sư thống kê tìm kiếm một tên gọi mới phản ánh đúng bản chất hiện đại của chương trình giảng dạy thống kê.
+ **Bản chất tiến trình (Process, not an Event):** Khoa học dữ liệu không phải là một sự kiện đơn lẻ mà là một **quy trình liên tục** sử dụng dữ liệu để thấu hiểu thế giới xung quanh.
+ **Giao thoa 3 lĩnh vực (Venn Diagram):**
  + **Computer Science / IT:** Kỹ năng lập trình, cấu trúc dữ liệu, hệ thống phần mềm.
  + **Math & Statistics:** Mô hình toán học, lý thuyết xác suất, thống kê suy luận.
  + **Domain / Business Knowledge:** Tri thức chuyên ngành, hiểu biết ngữ cảnh kinh doanh.
  + *Các giao điểm:* Machine Learning (CS + Math), Traditional Research (Math + Domain), Software Development (CS + Domain).
+ **Mục tiêu cốt lõi:** Làm bộc lộ các thông thái/tri thức ẩn (insights) và xu hướng đằng sau dữ liệu thô, chuyển đổi dữ liệu thành một **câu chuyện truyền cảm hứng (storytelling)** để giúp tổ chức đưa ra các quyết định chiến lược.

### 2. Bối cảnh bùng nổ Khoa học Dữ liệu Ngày nay
+ **Tài nguyên dồi dào:** Dữ liệu có dung lượng khổng lồ, thuật toán tiên tiến phát triển mạnh mẽ.
+ **Chi phí tối ưu:** Thuật toán mã nguồn mở (Open-source) miễn phí, chi phí lưu trữ và tính toán điện toán đám mây ngày càng rẻ và phổ biến.
+ **Thời điểm vàng:** Chưa bao giờ có thời điểm thuận lợi cho các nhà khoa học dữ liệu như hiện nay.

### 3. Nền tảng & Các bước tổng quan
+ **Nguồn dữ liệu đa dạng:** Log files, Email, Social media, Sales data, Patient records, Sports data, Sensor data, Security cameras.
+ **Vai trò với tổ chức:**
  + Thấu hiểu môi trường hoạt động.
  + Phân tích các vấn đề hiện hữu.
  + Phát hiện các cơ hội kinh doanh mới bị ẩn giấu.
+ **4 Bước tổng quát trong dự án Data Science:**
  + **Bước 1 (Quan trọng nhất):** Đặt câu hỏi tò mò để làm rõ nhu cầu nghiệp vụ của doanh nghiệp (Business Need).
  + **Bước 2:** Xác định dữ liệu cần thiết và nguồn thu thập (cấu trúc và phi cấu trúc).
  + **Bước 3:** Sử dụng nhiều mô hình phân tích để tìm kiếm mẫu (patterns).
  + **Bước 4:** Sử dụng công cụ trực quan hóa dữ liệu (Visualization) để truyền tải kết quả và đề xuất hành động cho stakeholders.

### 4. Lời khuyên cho Nhà khoa học Dữ liệu Mới (Advice for New Data Scientists)
+ **3 Phẩm chất tâm lý cốt lõi:**
  + **Curious (Tò mò):** Yếu tố bắt buộc số 1. Không tò mò sẽ không biết phải làm gì với dữ liệu.
  + **Argumentative (Hay tranh luận):** Khả năng lập luận giúp đưa ra các giả thuyết ban đầu, từ đó học hỏi từ dữ liệu để điều chỉnh giả thuyết.
  + **Judgmental (Mang tính đánh giá/Phán đoán):** Cần có những nhận định ban đầu để biết bắt đầu từ đâu.
+ **Thái độ học tập:** Không ngại thừa nhận giả thuyết ban đầu bị sai ("Tôi từng nghĩ X, nhưng dữ liệu cho thấy Y").
+ **Kỹ năng bắt buộc:**
  + Thành thạo ít nhất một nền tảng/phần mềm phân tích.
  + **Khả năng Kể chuyện (Storytelling):** Nếu không kể được câu chuyện hay từ dữ liệu, kết quả phân tích sẽ bị chôn vùi và không ai biết đến.
  + **Lợi thế cạnh tranh (Competitive Advantage):** Sự hiểu biết sâu sắc về một lĩnh vực cụ thể (Health, Education, Finance...) vượt trội hơn người khác.

---

## 📗 CHƯƠNG 1.2: INTRODUCTION TO DATA SCIENCE (PHẦN 2) - BÀI TOÁN & CASE STUDIES
*Nguồn: `1.2 Introduction to Data Science 2.pptx`*

### 1. Case Study 1: Ủy ban Giao thông Toronto (TTC) - Bài toán Khiếu nại & Thời tiết
+ **Bối cảnh:** TTC quản lý hệ thống giao thông công cộng tại Toronto và sở hữu tập dữ liệu 500,000 lượt khiếu nại (kết hợp dữ liệu phi cấu trúc như email/fax và dữ liệu có cấu trúc như thời gian, loại khiếu nại, người xử lý).
+ **Vấn đề:** Không tìm thấy quy luật hay lý do tại sao một số ngày lượng khiếu nại lại tăng đột biến.
+ **Khám phá bất ngờ (Serendipity & Curiosity):** Chuyên viên phân tích vô tình bước xuống xe bus trúng vũng nước mưa bất ngờ và cảm thấy rất bực bội. Anh nảy ra giả thuyết: *Liệu có mối liên hệ giữa thời tiết cực đoan và lượng khiếu nại?*
+ **Kết quả:** Kết hợp dữ liệu thời tiết từ Environment Canada cho thấy **10 ngày có lượng khiếu nại cao nhất trùng khớp hoàn toàn với những ngày thời tiết xấu bất ngờ** (mưa rào bất chợt, nhiệt độ giảm sâu, tuyết rơi giông lốc).
+ **Thông điệp:** Tin tốt là tìm ra nguyên nhân; Tin xấu là không thể thay đổi được thời tiết, nhưng giúp lãnh đạo hiểu rõ bản chất vấn đề.

### 2. Case Study 2: Uber - Định giá Động (Surge Pricing)
+ **Ứng dụng:** Uber thu thập dữ liệu thời gian thực (Real-time data) về số lượng tài xế khả dụng và nhu cầu khách hàng.
+ **Giải pháp:** Áp dụng thuật toán Surge Charge (tăng giá giờ cao điểm) để thu hút thêm tài xế đến khu vực đông khách, phân bổ đúng số lượng tài xế, đúng nơi, đúng thời điểm với chi phí khách hàng chấp nhận trả.

### 3. Case Study 3: Tối ưu hóa Giao thông Tàu điện (Streetcar Operations)
+ **Giải pháp:** Sử dụng dữ liệu cảm biến/định vị (probe data) và dữ liệu khiếu nại để phát hiện các điểm nghẽn giao thông giờ cao điểm.
+ **Kết quả:** Số giờ lãng phí trung bình hàng tháng của người đi làm do tắc đường đã giảm từ **4.75 giờ (năm 2010) xuống còn 3.0 giờ**.

### 4. Case Study 4: Dự báo Tảo độc ở Hồ nước ngọt (Cyanobacterial Blooms)
+ **Công nghệ:** Triển khai thuyền robot, phao cảm biến và drone gắn camera thu thập dữ liệu vật lý, hóa học, sinh học.
+ **Kết quả:** Xây dựng mô hình thuật toán dự báo thời điểm và vị trí bùng phát tảo độc, giúp bảo vệ nguồn nước sinh hoạt và khu du lịch sinh thái.

---

## 📙 CHƯƠNG 1.3: DATA SCIENCE TOPIC 1 - BIG DATA & NỀN TẢNG PHÂN TÍCH
*Nguồn: `1.3 Data Science topic 1 .pptx`*

### 1. Định nghĩa Big Data & Mô hình 5 V's
+ **Định nghĩa Ernst & Young:** Big Data là tập hợp dữ liệu động, quy mô lớn và đa dạng được tạo ra từ con người, công cụ và máy móc; đòi hỏi công nghệ đổi mới và có khả năng mở rộng để thu thập, lưu trữ và xử lý phân tích nhằm mang lại tri thức kinh doanh theo thời gian thực.
+ **Mô hình 5 V's cốt lõi:**
  1. **Velocity (Tốc độ):** Tốc độ dữ liệu tích lũy và phát sinh (VD: Mỗi 60 giây có hàng trăm giờ video được tải lên YouTube).
  2. **Volume (Dung lượng):** Quy mô dữ liệu cực lớn (VD: Hàng tỷ thiết bị di động/IoT tạo ra khoảng 2.5 quintillion bytes dữ liệu mỗi ngày).
  3. **Variety (Đa dạng):** Nhiều định dạng dữ liệu khác nhau (Văn bản, hình ảnh, âm thanh, dữ liệu y tế, cảm biến IoT).
  4. **Veracity (Độ tin cậy/Xác thực):** Tính chính xác và nguồn gốc dữ liệu. Khoảng **80% dữ liệu hiện nay là phi cấu trúc**, đòi hỏi kỹ thuật phân loại và làm sạch để đảm bảo độ tin cậy.
  5. **Value (Giá trị):** Giá trị kinh doanh thực tế trích xuất được từ dữ liệu.

### 2. Chuyển đổi Số (Digital Transformation) nhờ Big Data
+ **Khái niệm:** Sự thay đổi về tổ chức và văn hóa doanh nghiệp được thúc đẩy bởi Data Science và Big Data.
+ **Ví dụ thực tế:**
  + **Netflix:** Chuyển đổi từ dịch vụ cho thuê đĩa DVD qua bưu điện thành nền tảng xem phim trực tuyến hàng đầu thế giới.
  + **Houston Rockets (NBA):** Sử dụng camera trên cao phân tích các đường chuyền và vị trí ném rổ đạt hiệu suất cao nhất.
  + **Lufthansa:** Phân tích dữ liệu hành khách để cá nhân hóa dịch vụ hàng không.

### 3. Hệ sinh thái Hadoop
+ **Apache Hadoop:** Khung phần mềm mã nguồn mở hỗ trợ tính toán phân tán (distributed computing) trên các cụm máy tính (clusters) có khả năng mở rộng hàng nghìn máy.
+ **Đặc điểm:** Tự phát hiện và xử lý lỗi ở tầng ứng dụng (Application Layer Fault-tolerance) thay vì phụ thuộc vào phần cứng đắt tiền.

### 4. Tiến trình Phân tích Dữ liệu (Data Analysis vs Data Mining)
+ **5 Giai đoạn Phân tích Dữ liệu (Data Analysis):**
  1. Identify (Xác định dữ liệu cần phân tích)
  2. Collect (Thu thập dữ liệu)
  3. Clean (Làm sạch dữ liệu)
  4. Analyze (Phân tích dữ liệu)
  5. Interpret (Phiên dịch kết quả)
+ **4 Giai đoạn Khai phá Dữ liệu (Data Mining):**
  1. Data Gathering (Gom dữ liệu)
  2. Data Preparation (Tiền xử lý)
  3. Mining the Data (Áp dụng thuật toán khai phá)
  4. Data Analysis & Interpretation (Tạo mô hình phân tích thúc đẩy quyết định kinh doanh)

---

## 📕 CHƯƠNG 1.4: DATA SCIENCE TOPIC 2 - AI, MACHINE LEARNING & DEEP LEARNING
*Nguồn: `1.4 Data Science topic 2.pptx`*

### 1. Nền tảng Trí tuệ Nhân tạo (Artificial Intelligence - AI)
+ **Định nghĩa (John McCarthy):** AI là ngành khoa học và kỹ thuật chế tạo các máy tính thông minh, đặc biệt là các chương trình máy tính thông minh.
+ **Ứng dụng AI phổ biến:**
  + **Speech Recognition (ASR):** Chuyển đổi giọng nói thành văn bản nhờ NLP.
  + **Customer Service:** Trợ lý ảo (Virtual agents) hỗ trợ chăm sóc khách hàng tự động.
  + **Computer Vision:** Bóc tách thông tin ý nghĩa từ hình ảnh và video kỹ thuật số.
  + **Recommendation Engines:** Đề xuất sản phẩm/nội dung dựa trên hành vi tiêu dùng quá khứ.
  + **Automated Stock Trading:** Nền tảng giao dịch tần suất cao (High-frequency trading) không cần sự can thiệp của con người.

### 2. Machine Learning (Học máy) vs Deep Learning (Học sâu)
+ **Machine Learning:** Phân nhánh của AI sử dụng dữ liệu và thuật toán thống kê để bắt chước cách con người học tập, cải thiện độ chính xác theo thời gian.
+ **Deep Learning:** Tập con của Machine Learning, sử dụng **Mạng thần kinh nhân tạo (Neural Networks) có từ 3 lớp trở lên** (các lớp ẩn - hidden layers) để mô phỏng hoạt động não bộ con người.

### 3. Bảng So Sánh Chi Tiết ML vs DL

| Tiêu Chí So Sánh | Machine Learning (ML) | Deep Learning (DL) |
| :--- | :--- | :--- |
| **Dung lượng Dữ liệu (Data Requirement)** | Hoạt động tốt trên lượng dữ liệu vừa và nhỏ | Yêu cầu tập dữ liệu cực lớn để đạt hiệu năng |
| **Độ chính xác (Accuracy)** | Khá tốt, chạm mốc giới hạn khi dữ liệu tăng | Độ chính xác rất cao khi dữ liệu đủ lớn |
| **Thời gian Huấn luyện (Training Time)** | Tốn ít thời gian huấn luyện | Tốn nhiều thời gian huấn luyện (vài ngày/tuần) |
| **Phụ thuộc Phần cứng (Hardware)** | Chạy tốt trên CPU thông thường | Yêu cầu cấu hình phần cứng mạnh (GPU / TPU) |
| **Tinh chỉnh (Hyperparameter Tuning)** | Giới hạn khả năng tinh chỉnh | Có thể tinh chỉnh theo nhiều cách phức tạp |
| **Phân loại Thuật toán (Types)** | Supervised, Unsupervised, Reinforcement Learning | CNN (Convolutional), RNN (Recurrent Neural Networks) |

---

## 📘 CHƯƠNG 2.1: DATA SCIENCE METHODOLOGY - FROM PROBLEM TO ANALYTIC APPROACH
*Nguồn: `2.1 Data science- From Problem to Approach.pptx`*

```
[Business Understanding] ➔ [Analytic Approach] ➔ [Data Requirements] ➔ [Data Collection]
         ▲                                                                      │
         │                                                                      ▼
    [Feedback] ◄────── [Deployment] ◄────── [Evaluation] ◄────── [Modeling] ◄───┤ (Data Prep)
```

### 1. Giai đoạn 1: Business Understanding (Hiểu bài toán Kinh doanh)
+ **Tầm quan trọng:** Là bước khởi đầu bắt buộc. Việc làm rõ mục tiêu (Goal) và các mục tiêu cụ thể (Objectives) giúp xác định đúng loại dữ liệu cần thu thập.
+ **Hành động cốt lõi:** Dành thời gian thảo luận với các bên liên quan (Stakeholders) để đặt ra **câu hỏi nghiên cứu rõ ràng**.

### 2. Case Study Y Tế: Bệnh nhân Suy tim (Congestive Heart Failure - CHF)
+ **Bối cảnh:** Công ty bảo hiểm y tế Mỹ đứng trước rủi ro cắt giảm ngân sách hỗ trợ tài chính cho bệnh nhân tái nhập viện.
+ **Số liệu:** 30% bệnh nhân cai nghiện/phục hồi tái nhập viện trong 1 năm; 50% tái nhập viện trong 5 năm.
+ **Mục tiêu kinh doanh (Business Requirements):**
  1. Dự đoán kết quả tái nhập viện CHF (Có / Không) cho từng bệnh nhân.
  2. Dự đoán mức độ rủi ro tái nhập viện (Risk score).
  3. Hiểu rõ chuỗi sự kiện dẫn đến nguy cơ tái nhập viện.
  4. Dễ dàng giải thích và áp dụng cho bác sĩ/lâm sàng.

### 3. Giai đoạn 2: Analytic Approach (Lựa chọn Phương pháp Phân tích)
+ **Phân loại câu hỏi & Phương pháp tương ứng:**
  + **Descriptive (Mô tả):** Nhắm đến trạng thái hiện tại ("Current status").
  + **Diagnostic / Statistical (Chẩn đoán):** Phân tích sự kiện đã xảy ra và nguyên nhân ("What happened & Why?").
  + **Predictive (Dự báo):** Dự đoán xu hướng và xác suất tương lai ("What will happen next?").
  + **Prescriptive (Đề xuất):** Đưa ra giải pháp tối ưu ("How do we solve it?").
  + **Classification (Phân loại):** Dành cho câu hỏi dạng Có/Không (Yes/No).
  + **Clustering / Association (Gom nhóm):** Tìm kiếm hành vi/mẫu hình nhóm người.
+ **Lựa chọn cho Case Study CHF:** Chọn **Mô hình Phân loại Cây quyết định (Decision Tree Classification)** vì kết quả trực quan, minh bạch, giúp bác sĩ dễ dàng hiểu được các điều kiện gây ra rủi ro cao để can thiệp kịp thời.

---

## 📗 CHƯƠNG 2.2: DATA SCIENCE METHODOLOGY - FROM REQUIREMENTS TO DATA COLLECTION
*Nguồn: `2.2 Data science-From Requirements to Collection.pptx`*

### 1. Giai đoạn 3: Data Requirements (Yêu cầu Dữ liệu)
+ **Ví dụ Nấu ăn (Spaghetti Analogy):** Nếu mục tiêu là nấu món mỳ Ý, dữ liệu chính là nguyên liệu. Cần xác định đúng nguyên liệu, cách tìm, cách làm sạch và chế biến.
+ **Yêu cầu đối với Case Study CHF:**
  + **Tiêu chí chọn nhóm bệnh nhân (Cohort):** Bệnh nhân nội trú trong khu vực phục vụ; có chẩn đoán chính là CHF trong 1 năm liên tục; có bảo hiểm liên tục ít nhất 6 tháng trước đó.
  + **Cấu trúc dữ liệu:** 1 dòng đại diện cho 1 bệnh nhân; các cột chứa biến lịch sử lâm sàng (chẩn đoán, xét nghiệm, đơn thuốc, lịch sử nhập viện).Một bệnh nhân có thể có hàng nghìn bản ghi thô.

### 2. Giai đoạn 4: Data Collection (Thu thập Dữ liệu)
+ **Nguồn thu thập:** Thông tin nhân khẩu học, hồ sơ lâm sàng, bảo hiểm, chi phí điều trị, dữ liệu dược phẩm.
+ **Xử lý Dữ liệu Thiếu/Chưa sẵn sàng:**
  + Trong case study CHF, dữ liệu sử dụng thuốc (Drug data) chưa được tích hợp vào CSDL chung.
  + **Nguyên tắc:** Có thể hoãn thu thập các dữ liệu chưa có sẵn. Đội ngũ vẫn tiến hành xây dựng mô hình thử nghiệm. Thực tế mô hình CHF đạt kết quả rất tốt ngay cả khi chưa có dữ liệu thuốc.
+ **Hành động kỹ thuật:** Trích xuất dữ liệu từ nhiều nguồn, hợp nhất, loại bỏ dữ liệu dư thừa (reduntant data) và tự động hóa quy trình truy vấn CSDL.

---

## 📙 CHƯƠNG 2.3: DATA SCIENCE METHODOLOGY - FROM UNDERSTANDING TO DATA PREPARATION
*Nguồn: `2.3 Data science- From Understanding to Preparation.pptx`*

### 1. Giai đoạn 5: Data Understanding (Thấu hiểu Dữ liệu)
+ **Mục tiêu cốt lõi:** Trả lời câu hỏi: *Dữ liệu thu thập được có đại diện đúng cho bài toán cần giải quyết không?*
+ **Công cụ Thống kê Mô tả áp dụng:**
  + **Univariate Statistics:** Tính Mean, Median, Min, Max, Standard Deviation cho từng biến.
  + **Pairwise Correlations:** Kiểm tra mối tương quan cặp. Nếu hai biến có tương quan cực kỳ cao, chúng bị dư thừa (redundant) -> chỉ giữ lại 1 biến.
  + **Histograms (Biểu đồ tần suất):** Xem xét dạng phân bố của biến, phát hiện giá trị ngoại lệ (outliers) hoặc dữ liệu khuyết thiếu (missing values) để lên kế hoạch xử lý.

### 2. Giai đoạn 6: Data Preparation (Tiền xử lý Dữ liệu)
+ **Tỷ lệ thời gian:** Là giai đoạn tốn nhiều thời gian nhất trong dự án Data Science, chiếm từ **70% đến 90% tổng thời gian dự án** (Tự động hóa CSDL có thể giảm xuống 50%).
+ **Các công việc chính trong Data Preparation:**
  1. **Làm sạch (Cleaning):** Xử lý giá trị thiếu (missing values), loại bỏ giá trị không hợp lệ, xóa bản ghi trùng lặp (duplicates).
  2. **Biến đổi (Transformation):** Đưa dữ liệu về dạng dễ làm việc hơn (ví dụ: băm nhỏ dữ liệu như thái hành tây để gia vị ngấm nhanh hơn).
  3. **Kỹ nghệ Đặc trưng (Feature Engineering):** Sử dụng tri thức ngành (domain knowledge) để tạo ra các thuộc tính/biến mới giúp thuật toán ML học hiệu quả hơn.
  4. **Xử lý văn bản (Text Analysis Steps):** Tách từ, mã hóa văn bản thành ma trận số học.

---

## 📕 CHƯƠNG 2.4: DATA SCIENCE METHODOLOGY - FROM MODELING TO EVALUATION
*Nguồn: `2.4 Data science- From Modeling to Evaluation.pptx`*

### 1. Giai đoạn 7: Modeling (Xây dựng Mô hình)
+ **Bản chất:** Là bước "nếm thử nước sốt" xem đã chuẩn vị chưa hay cần nêm nếm thêm gia vị.
+ **Sử dụng Tập huấn luyện (Training Set):** Dữ liệu lịch sử đã biết trước kết quả chuẩn để huấn luyện và hiệu chỉnh (calibrate) thông số mô hình.
+ **Thử nghiệm nhiều thuật toán:** Thử nghiệm nhiều thuật toán khác nhau để xác định chính xác các biến quan trọng.

### 2. Giai đoạn 8: Evaluation (Đánh giá Mô hình)
+ **Mục tiêu:** Kiểm tra chất lượng mô hình và đảm bảo mô hình thực sự trả lời đúng câu hỏi kinh doanh ban đầu trước khi triển khai thực tế.
+ **2 Pha Đánh giá Chính:**
  + **Pha 1 - Diagnostic Measures (Đo lường Chẩn đoán):** Kiểm tra xem mô hình có hoạt động đúng thiết kế không (ví dụ: dùng ma trận nhầm lẫn Confusion Matrix, độ chính xác Precision/Recall đối với Decision Tree).
  + **Pha 2 - Statistical Significance Testing (Kiểm định Ý nghĩa Thống kê):** Kiểm định tính vững của mô hình, đảm bảo kết quả không phải do ngẫu nhiên.

---

## 📘 CHƯƠNG 2.5: DATA SCIENCE METHODOLOGY - FROM DEPLOYMENT TO FEEDBACK
*Nguồn: `2.5 Data science- From Deployment to Feedback.pptx`*

### 1. Giai đoạn 9: Deployment (Triển khai)
+ **Phương thức:** Sau khi mô hình đạt đánh giá, mô hình được triển khai vào môi trường thử nghiệm (Test environment) hoặc áp dụng cho một nhóm người dùng giới hạn (Limited group) để củng cố độ tin cậy.
+ **Ví dụ thực tế:**
  + Bản đồ dự báo rủi ro nhập viện do tiểu đường ở thanh thiếu niên (Juvenile Diabetes Hospitalization Risk Map).
  + Hệ thống đánh giá rủi ro bệnh nhân CHF theo thời gian thực cho bác sĩ lâm sàng.

### 2. Giai đoạn 10: Feedback (Phản hồi & Cải tiến Liên tục)
+ **Vòng lặp khép kín (Feedback Loop):** Thu thập phản hồi từ người dùng cuối (Bác sĩ, khách hàng, tư vấn viên) để tinh chỉnh mô hình.
+ **Nguyên lý:** "Càng biết nhiều, bạn sẽ càng muốn biết thêm". Giá trị của mô hình phụ thuộc vào việc liên tục cập nhật dữ liệu mới và điều chỉnh thuật toán theo thời gian.
+ **Đánh giá hiệu quả:** So sánh tỷ lệ tái nhập viện thực tế của bệnh nhân **TRƯỚC và SAU** khi áp dụng mô hình can thiệp.

---

## 📗 CHƯƠNG 2.6: PRACTICAL DATA SCIENCE STEPS IN PYTHON (DATA WRANGLING & PREPROCESSING)
*Nguồn: `2.6 Data science steps_1.pptx`*

### 1. Nhập / Xuất Dữ liệu trong Python (Pandas IO)

```python
import pandas as pd

# 1. Nhập dữ liệu (Importing Data)
df_csv = pd.read_csv("data.csv")
df_json = pd.read_json("data.json")
df_excel = pd.read_excel("data.xlsx")
df_sql = pd.read_sql("SELECT * FROM table", connection)

# 2. Xuất dữ liệu (Exporting Data)
df.to_csv("/workspace/scratch/output.csv", index=False)
df.to_json("/workspace/scratch/output.json")
df.to_excel("/workspace/scratch/output.xlsx")
```

### 2. Xử lý Dữ liệu Khuyết Thiếu (Handling Missing Values)
+ **Dấu hiệu nhận biết:** `"?"`, `"N/A"`, `NaN`, ô trống.
+ **Các chiến lược xử lý:**
  + **Drop (Xóa):** Xóa biến/cột nếu thiếu quá nhiều; Xóa dòng/bản ghi (`df.dropna()`).
  + **Replace (Thay thế):** Thay bằng giá trị trung bình Mean (cho biến số), Thay bằng Tần suất Mode (cho biến phân loại), hoặc Interpolation (Nội suy).
  + **Keep (Giữ nguyên):** Để nguyên giá trị khuyết nếu mô hình hỗ trợ.

### 3. Chuẩn hóa Định dạng Dữ liệu (Data Formatting)
+ Ép các biểu diễn khác nhau về cùng một chuẩn (Ví dụ: `"NY"`, `"N.Y."`, `"New York"` ➔ `"New York"`).

### 4. Chuẩn hóa Thang đo Dữ liệu (Data Normalization)
Giúp các biến có khoảng giá trị khác nhau (ví dụ: `Age`: 20-40, `Income`: 20,000-500,000) về cùng một khoảng giá trị tương đương để không làm lệch mô hình.

1. **Simple Feature Scaling:**
   $$x_{new} = \frac{x_{old}}{x_{max}}$$

2. **Min-Max Normalization (Chuyển về khoảng [0, 1]):**
   $$x_{new} = \frac{x_{old} - x_{min}}{x_{max} - x_{min}}$$

3. **Z-Score Standardization (Chuyển về phân bố chuẩn Mean=0, Std=1):**
   $$x_{new} = \frac{x_{old} - \mu}{\sigma}$$

### 5. Nhóm khoảng Dữ liệu (Binning)
Chuyển đổi biến số liên tục thành biến phân loại danh mục (Categorical).
+ *Ví dụ:* Cột `Price` từ `5000` đến `45000` được chia thành 3 bins: `Low`, `Medium`, `High` bằng hàm `pd.cut()`.

### 6. Mã hóa Biến Phân loại (Categorical Dummy Variables / One-Hot Encoding)
+ **Vấn đề:** Đa số mô hình thống kê/ML không thể nhận đầu vào là chuỗi String.
+ **Giải pháp:** Tạo biến giả (Dummy Variables), gán giá trị `1` hoặc `0` cho mỗi danh mục duy nhất bằng `pd.get_dummies()`.

---

## 🛠️ TỔNG HỢP CHEAT SHEET LẬP TRÌNH PANDAS CHO AGENTS

```python
import pandas as pd
import numpy as np

# 1. Kiểm tra & Xử lý Missing Values
df.isnull().sum()
df['normalized-losses'].fillna(df['normalized-losses'].mean(), inplace=True)
df.dropna(subset=['price'], axis=0, inplace=True)

# 2. Min-Max Normalization
df['length'] = (df['length'] - df['length'].min()) / (df['length'].max() - df['length'].min())

# 3. Z-Score Standardization
df['height'] = (df['length'] - df['length'].mean()) / df['length'].std()

# 4. Binning trong Pandas
bins = np.linspace(min(df['price']), max(df['price']), 4)
group_names = ['Low', 'Medium', 'High']
df['price-binned'] = pd.cut(df['price'], bins, labels=group_names, include_lowest=True)

# 5. One-Hot Encoding
dummy_fuel = pd.get_dummies(df['fuel-type'])
df = pd.concat([df, dummy_fuel], axis=1)
```

---
*Tài liệu Knowledge Base này được tổng hợp đầy đủ và chính xác 100% dựa trên nội dung 10 file slide bài giảng môn ADY201m.*
