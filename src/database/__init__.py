"""Module tương tác và đồng bộ CSDL Microsoft SQL Server 3NF (Phase L - Load)."""
from __future__ import annotations

__all__ = [
    "FEATURE_COLUMNS",
    "build_connection_string",
    "execute_schema",
    "feature_values",
    "get_connection",
    "import_record",
    "load_processed_records",
    "main",
    "split_sql_batches",
    "sync_records",
    "update_record",
    "verify_database",
]


def __getattr__(name: str):
    from . import sqlserver
    if hasattr(sqlserver, name):
        return getattr(sqlserver, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
