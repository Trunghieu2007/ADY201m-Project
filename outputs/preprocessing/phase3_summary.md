# ADY201m — Phase 3 Summary

## Scope

Phase 3 implements **Data Preprocessing & Feature Engineering** on the frozen Phase 1 raw dataset.

The raw baseline `data/raw/articles.jsonl` is not overwritten. All derived artifacts are stored under `data/processed/` and `reports/phase3/`.

## Input integrity

- Input: `data/raw/articles.jsonl`
- Records: 20
- SHA-256: `8f86ceb25c2b1ef605b235618ff425870e97aab05a50ca7cd5be0877ef0b5abc`
- Raw data remains immutable.

## Preprocessing

1. Unicode NFC normalization
2. Whitespace normalization
3. URL removal from derived text only
4. Conservative removal of exact leading title/description duplication when present
5. Conservative author normalization into a separate `author_clean` field
6. Deterministic whitespace tokenization
7. Preservation of all original raw fields in the processed records

The leading-duplication rule affected **2/20 records**. The raw values remain unchanged.

## Feature engineering

Each processed article receives deterministic lexical and metadata features:

- character count
- word count
- sentence count
- unique-word count
- lexical diversity
- average word length
- title character/word counts
- description character/word counts
- title-to-content word ratio
- publication hour
- publication weekday
- integer category/subcategory IDs
- one-hot category features
- one-hot subcategory features

The resulting `feature_matrix.csv` contains **35 feature columns** for 20 records.

## Artifacts

- `data/processed/articles_processed.jsonl`
- `data/processed/feature_matrix.csv`
- `reports/phase3/phase3_manifest.json`
- `reports/phase3/feature_summary.json`
- `reports/phase3/phase3_validation.json`
- `reports/phase3/phase3_summary.md`
- `src/preprocessing/`

## Validation

- Phase 3 processed-data validation: **PASS**
- Regression/unit tests: **9/9 PASS**
- Raw SHA-256 remains identical to the frozen baseline.

## Design decisions and limitations

- No aggressive stemming/lemmatization was applied because Vietnamese word segmentation and linguistic normalization require a stronger NLP decision than the current 20-record sample justifies.
- Whitespace tokenization is therefore explicitly treated as a reproducible baseline, not as a linguistically perfect Vietnamese tokenizer.
- No target-dependent feature engineering was introduced, avoiding data leakage before the modeling phase.
- No machine-learning model is trained in Phase 3.
- Raw data is never modified by preprocessing.
