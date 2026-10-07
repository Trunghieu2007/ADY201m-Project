# ADY201m — Exploratory Data Analysis

## 1. Mục tiêu

Phân tích tập trung vào mô tả và khám phá dataset thông qua EDA. Không thực hiện machine learning, classification, regression hoặc prediction.

## 2. Dataset

- Raw dataset: `data\raw\articles.json`
- Số records: 40

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
- `author`: 1 missing
- `publisher`: 0 missing
- `published_at`: 0 missing
- `category`: 0 missing
- `subcategory`: 1 missing
- `article_id`: 0 missing
- `crawled_at`: 0 missing
- `source`: 0 missing

## 6. Category distribution

- Bất động sản: 8
- Khoa học công nghệ: 8
- Kinh doanh: 8
- Sức khỏe: 8
- Thời sự: 8

## 7. Subcategory distribution

- Chính sách: 4
- Tin tức: 4
- AI: 3
- Các bệnh: 3
- Thời sự: 3
- Chính trị: 2
- Chứng khoán: 2
- Doanh nghiệp: 2
- Quốc tế: 2
- (missing): 1
- Bất động sản: 1
- Chuyển đổi số: 1
- Giao thông: 1
- Hàng hóa: 1
- Ngoại thất: 1
- Nhịp sống số: 1
- Nội thất: 1
- Sống khỏe: 1
- Thiết bị: 1
- Thế giới tự nhiên: 1
- Thị trường: 1
- Vĩ mô: 1
- Đầu tư: 1
- Đổi mới sáng tạo: 1

## 8. Text statistics

### content_char_count
- Count: 40
- Min: 1432
- Max: 8200
- Mean: 3446.82
- Median: 3039.5
- Standard deviation: 1750.65
- Q1: 1986.25
- Q3: 4060.5

### content_word_count
- Count: 40
- Min: 300
- Max: 1834
- Mean: 753.1
- Median: 657.0
- Standard deviation: 393.04
- Q1: 435.25
- Q3: 896.25

### content_sentence_count
- Count: 40
- Min: 10
- Max: 104
- Mean: 30.95
- Median: 25.5
- Standard deviation: 19.39
- Q1: 19.0
- Q3: 35.75

### content_unique_word_count
- Count: 40
- Min: 192
- Max: 533
- Mean: 302.38
- Median: 285.0
- Standard deviation: 80.12
- Q1: 245.25
- Q3: 341.0

### content_avg_word_length
- Count: 40
- Min: 3.11
- Max: 3.71
- Mean: 3.45
- Median: 3.43
- Standard deviation: 0.13
- Q1: 3.37
- Q3: 3.53

### title_word_count
- Count: 40
- Min: 5
- Max: 16
- Mean: 11.25
- Median: 11.5
- Standard deviation: 2.91
- Q1: 9.0
- Q3: 13.75

### description_word_count
- Count: 40
- Min: 22
- Max: 58
- Mean: 32.17
- Median: 31.0
- Standard deviation: 6.63
- Q1: 29.0
- Q3: 35.75

## 9. Category × text statistics

### Bất động sản
- Articles: 8
- Mean word count: 836.25
- Median word count: 624.5
- Min word count: 393
- Max word count: 1674

### Khoa học công nghệ
- Articles: 8
- Mean word count: 560.25
- Median word count: 521.5
- Min word count: 374
- Max word count: 987

### Kinh doanh
- Articles: 8
- Mean word count: 660.75
- Median word count: 614.0
- Min word count: 300
- Max word count: 1180

### Sức khỏe
- Articles: 8
- Mean word count: 749.5
- Median word count: 711.0
- Min word count: 429
- Max word count: 1294

### Thời sự
- Articles: 8
- Mean word count: 958.75
- Median word count: 840.5
- Min word count: 417
- Max word count: 1834

## 10. Temporal analysis

### Publication date
- 2026-09-24: 14
- 2026-09-25: 6
- 2026-10-05: 20

### Publication hour
- 00:00: 7
- 01:00: 2
- 05:00: 5
- 06:00: 4
- 07:00: 2
- 08:00: 2
- 09:00: 6
- 14:00: 1
- 15:00: 2
- 16:00: 2
- 18:00: 1
- 19:00: 2
- 20:00: 4

### Publication-to-crawl timestamp gap
- Min: 9.88 minutes
- Mean: 318.11 minutes
- Median: 282.62 minutes
- Max: 1006.55 minutes
- Negative gaps: 0
> This is `crawled_at - published_at`; it is not a direct benchmark of crawler execution latency.

## 11. Metadata

- Unique authors: 32
- Unique publishers: 1
- Unique sources: 1
- Unique article IDs: 40

## 12. Visualizations

- `outputs/eda/category_subcategory.png`
- `outputs/eda/average_words_by_category.png`
- `outputs/eda/publication_hour.png`
- `outputs/eda/publication_to_crawl_gap_by_category.png`
- `outputs/eda/content_length_distribution.png`
- `outputs/eda/word_count_distribution.png`

## 13. Interpretation limitation

All descriptive findings apply only to the 40-record dataset analyzed in this project. They must not be generalized to the entire VnExpress website or population of articles.

## 14. Status

**STATUS: COMPLETE — REPRODUCIBLE DESCRIPTIVE EDA PIPELINE**
