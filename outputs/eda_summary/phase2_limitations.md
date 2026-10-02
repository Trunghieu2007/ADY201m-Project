# ADY201m — EDA Limitations

## 1. Sample size
The current dataset contains 20 records. Statistics are descriptive
statistics of this dataset only and are not population estimates.

## 2. Sampling
The dataset is a collected sample rather than a statistically random sample of all
VnExpress articles. Distributional results may therefore differ from the broader corpus.

## 3. Text metrics
Word count uses whitespace-separated tokens. Sentence count is an approximate punctuation-based
measure. These metrics are suitable for descriptive EDA but are not full Vietnamese NLP tokenization.

## 4. Unique-word statistics
Unique-word statistics use normalized tokens only for measurement. The raw dataset is not modified.

## 5. Temporal interpretation
Publication-to-crawl timestamp gap is calculated as `crawled_at - published_at`. It does not directly
measure crawler execution time.

## 6. Metadata
Author, publisher, source and article-ID distributions describe only values present in the collected sample.

## 7. Raw-data integrity
EDA does not modify `data/raw/articles.jsonl`. Future cleaning or normalization should create outputs under
`data/processed/` and keep transformations traceable.
