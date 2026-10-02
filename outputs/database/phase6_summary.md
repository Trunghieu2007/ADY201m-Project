# ADY201m — Phase 6 Summary

## Scope
Microsoft SQL Server integration. Streamlit is explicitly deferred to Phase 7 or 8.

## Implemented
- SQL Server bootstrap guidance: `sql/create_database.sql`
- Idempotent table/index creation: `sql/create_tables.sql`
- Parameterized update/insert query contract: `sql/upsert_article.sql`
- Analysis/query examples: `sql/queries.sql`
- Connection/configuration helper: `src/database/sqlserver.py`
- Phase runner: `src/database/run_phase6.py`
- 13 approved non-target-derived numeric features mapped to `dbo.ArticleFeatures`
- Normalized `Categories`, `Subcategories`, and `Authors` dimensions with foreign keys
- `Articles` as the canonical article table keyed by source `article_id`
- Transactional import/update/sync paths

## Execution order
```powershell
# Optional: create the database in SSMS while connected to master
# Then configure SQL Server connection settings.
python -m src.database.run_phase6 --init-schema
python -m src.database.run_phase6 --import
python -m src.database.run_phase6 --update
# Or one idempotent pass:
python -m src.database.run_phase6 --sync
```

## Runtime boundary
The repository is prepared for a real Microsoft SQL Server connection, but the build container does not contain a live SQL Server instance and does not have `pyodbc` installed. Therefore this completion records **code/readiness and offline validation**, not a fabricated successful remote database import.

## Streamlit boundary
The former dashboard was moved to `future/phase7_streamlit/dashboard/` and its dependency was moved to `requirements-streamlit.txt`. Phase 6 tests deliberately assert that Streamlit is not the active persistence layer.

## Data integrity
`data/raw/articles.jsonl` and `data/processed/articles_processed.jsonl` remain input sources and are not rewritten by the SQL layer.
