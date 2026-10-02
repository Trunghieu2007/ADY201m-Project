from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .sqlserver import (
    PROCESSED_JSONL,
    SCHEMA_SQL,
    UPSERT_SQL,
    execute_schema,
    get_connection,
    import_record,
    load_processed_records,
    update_record,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "outputs" / "database" / "database_manifest.json"
SUMMARY = ROOT / "outputs" / "database" / "database_summary.md"


# Thực hiện tạo cấu trúc bảng, nhập mới hoặc cập nhật bản ghi vào CSDL SQL Server
def run(*, init_schema: bool, do_import: bool, do_update: bool) -> dict:
    records = load_processed_records()
    connection = get_connection()
    stats = {"records_loaded": len(records), "schema_batches": 0, "inserted": 0, "updated": 0, "skipped": 0}
    try:
        cursor = connection.cursor()
        if init_schema:
            stats["schema_batches"] = execute_schema(cursor)
            connection.commit()
        if do_import:
            for record in records:
                if import_record(cursor, record):
                    stats["inserted"] += 1
                else:
                    stats["skipped"] += 1
            connection.commit()
        if do_update:
            for record in records:
                if update_record(cursor, record):
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1
            connection.commit()
        cursor.close()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return stats


# Giao diện dòng lệnh CLI đồng bộ cơ sở dữ liệu Microsoft SQL Server
def main() -> int:
    parser = argparse.ArgumentParser(description="ADY201m — Microsoft SQL Server Database Runner")
    parser.add_argument("--init-schema", action="store_true", help="Create missing tables/indexes")
    parser.add_argument("--import", dest="do_import", action="store_true", help="Insert missing processed records")
    parser.add_argument("--update", dest="do_update", action="store_true", help="Update records already in SQL Server")
    parser.add_argument("--sync", action="store_true", help="Run update-then-insert synchronization")
    args = parser.parse_args()

    if not any((args.init_schema, args.do_import, args.do_update, args.sync)):
        parser.error("Choose at least one operation: --init-schema, --import, --update, or --sync")

    if args.sync:
        connection = get_connection()
        try:
            cursor = connection.cursor()
            schema_batches = execute_schema(cursor)
            records = load_processed_records()
            inserted = updated = 0
            for record in records:
                if update_record(cursor, record):
                    updated += 1
                elif import_record(cursor, record):
                    inserted += 1
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        stats = {"records_loaded": len(records), "schema_batches": schema_batches, "inserted": inserted, "updated": updated}
    else:
        stats = run(init_schema=args.init_schema, do_import=args.do_import, do_update=args.do_update)

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "module": "Microsoft SQL Server integration",
        "status": "COMPLETE_CODE_READY",
        "scope": ["schema creation", "initial import", "parameterized update", "optional synchronization"],
        "input": str(PROCESSED_JSONL.relative_to(ROOT)),
        "schema": str(SCHEMA_SQL.relative_to(ROOT)),
        "update_query": str(UPSERT_SQL.relative_to(ROOT)),
        "records_available": len(load_processed_records()),
        "operations": stats,
        "database_runtime_note": "Actual server import requires a configured SQL Server and installed ODBC driver.",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY.write_text(
        "# ADY201m — Database Persistence Summary\n\n"
        "Microsoft SQL Server persistence layer for Vietnamese news analytics.\n\n"
        f"Records available: {len(load_processed_records())}.\n\n"
        "Supports schema creation, first import, explicit UPDATE synchronization and combined sync.\n",
        encoding="utf-8",
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print("Connection string source:", "ADY_SQLSERVER_CONNECTION_STRING" if os.getenv("ADY_SQLSERVER_CONNECTION_STRING") else "individual ADY_SQLSERVER_* variables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
