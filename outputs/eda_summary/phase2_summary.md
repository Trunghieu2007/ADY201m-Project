# ADY201m — Exploratory Data Analysis

## 1. Mục tiêu

Phân tích tập trung vào mô tả và khám phá dataset thông qua EDA. Không thực hiện machine learning, classification, regression hoặc prediction.

## 2. Dataset

- Raw dataset: `data\raw\articles.jsonl`
- Số records: 20
- SHA-256 hiện tại: `8f86ceb25c2b1ef605b235618ff425870e97aab05a50ca7cd5be0877ef0b5abc`
- Raw dataset không được chỉnh sửa trong EDA.

## 3. Schema

- Expected fields: 12
- Tất cả records có đủ expected fields: True
- Tất cả records match exact schema: True

- `url`
- `title`
- `description`
- `content`
- `author`
- `publisher`
- `published_at`
- `category`
- `subcategory`
- `article_id`
- `crawled_at`
- `source`

## 4. Duplicate analysis

- Duplicate `url`: 0
- Duplicate `title`: 0
- Duplicate `article_id`: 0

## 5. Missingness

- `url`: 0 missing
- `title`: 0 missing
- `description`: 0 missing
- `content`: 0 missing
- `author`: 0 missing
- `publisher`: 0 missing
- `published_at`: 0 missing
- `category`: 0 missing
- `subcategory`: 0 missing
- `article_id`: 0 missing
- `crawled_at`: 0 missing
- `source`: 0 missing

## 6. Category distribution

- Bất động sản: 4
- Khoa học công nghệ: 4
- Kinh doanh: 4
- Sức khỏe: 4
- Thời sự: 4

## 7. Subcategory distribution

- Chính sách: 3
- AI: 2
- Các bệnh: 2
- Thời sự: 2
- Chính trị: 1
- Chứng khoán: 1
- Doanh nghiệp: 1
- Hàng hóa: 1
- Ngoại thất: 1
- Quốc tế: 1
- Sống khỏe: 1
- Thế giới tự nhiên: 1
- Tin tức: 1
- Đầu tư: 1
- Đổi mới sáng tạo: 1

## 8. Text statistics

### character_count
- Count: 20
- Min: 1593
- Max: 8200
- Mean: 3128
- Median: 2600.5
- Standard deviation: 1853.36
- Q1: 1845.75
- Q3: 3569.5

### word_count
- Count: 20
- Min: 330
- Max: 1834
- Mean: 679.95
- Median: 556.0
- Standard deviation: 413.2
- Q1: 409.5
- Q3: 743.75

### sentence_count
- Count: 20
- Min: 10
- Max: 104
- Mean: 29.1
- Median: 22.0
- Standard deviation: 22.98
- Q1: 16.75
- Q3: 30.75

### unique_word_count
- Count: 20
- Min: 195
- Max: 413
- Mean: 272.95
- Median: 272.0
- Standard deviation: 56.42
- Q1: 231.75
- Q3: 315.5

### average_word_length
- Count: 20
- Min: 3.28
- Max: 3.71
- Mean: 3.46
- Median: 3.44
- Standard deviation: 0.13
- Q1: 3.35
- Q3: 3.57

### title_character_count
- Count: 20
- Min: 19
- Max: 67
- Mean: 46.95
- Median: 50.0
- Standard deviation: 12.79
- Q1: 36.75
- Q3: 54.75

### title_word_count
- Count: 20
- Min: 5
- Max: 15
- Mean: 10.45
- Median: 11.0
- Standard deviation: 2.93
- Q1: 8.0
- Q3: 13.0

### description_character_count
- Count: 20
- Min: 113
- Max: 178
- Mean: 143.5
- Median: 142.5
- Standard deviation: 18.82
- Q1: 127.25
- Q3: 162.5

### description_word_count
- Count: 20
- Min: 23
- Max: 40
- Mean: 31.45
- Median: 31.5
- Standard deviation: 4.85
- Q1: 27.0
- Q3: 35.0

## 9. Category × text statistics

### Bất động sản
- Articles: 4
- Mean word count: 730.5
- Median word count: 427.5
- Min word count: 393
- Max word count: 1674

### Khoa học công nghệ
- Articles: 4
- Mean word count: 515.75
- Median word count: 531.5
- Min word count: 374
- Max word count: 626

### Kinh doanh
- Articles: 4
- Mean word count: 560.75
- Median word count: 441.0
- Min word count: 330
- Max word count: 1031

### Sức khỏe
- Articles: 4
- Mean word count: 649.5
- Median word count: 711.0
- Min word count: 429
- Max word count: 747

### Thời sự
- Articles: 4
- Mean word count: 943.25
- Median word count: 761.0
- Min word count: 417
- Max word count: 1834

## 10. Temporal analysis

### Publication date
- 2026-09-24: 14
- 2026-09-25: 6

### Publication hour
- 00:00: 4
- 01:00: 2
- 08:00: 1
- 09:00: 1
- 14:00: 1
- 15:00: 2
- 16:00: 2
- 18:00: 1
- 19:00: 2
- 20:00: 4

### Publication-to-crawl timestamp gap
- Min: 9.88 minutes
- Mean: 365.97 minutes
- Median: 324.47 minutes
- Max: 1006.55 minutes
- Negative gaps: 0
> This is `crawled_at - published_at`; it is not a direct benchmark of crawler execution latency.

## 11. Metadata

- Unique authors: 18
- Unique publishers: 1
- Unique sources: 1
- Unique article IDs: 20

## 12. Visualizations

- `outputs/eda/category_subcategory.png`
- `outputs/eda/average_words_by_category.png`
- `outputs/eda/publication_hour.png`
- `outputs/eda/publication_to_crawl_gap_by_category.png`
- `outputs/eda/content_length_distribution.png`
- `outputs/eda/word_count_distribution.png`

## 13. Interpretation limitation

All descriptive findings apply only to the 20-record dataset analyzed in this project. They must not be generalized to the entire VnExpress website or population of articles.

## 14. Status

**STATUS: COMPLETE — REPRODUCIBLE DESCRIPTIVE EDA PIPELINE**
