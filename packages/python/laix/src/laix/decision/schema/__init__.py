"""The versioned record set, schema generator and structural validator."""

from __future__ import annotations

from .build import SCHEMA_ID, SCHEMA_PATH, build_schema, dumps_schema, write_schema
from .check import check
from .records import RECORDS, RECORD_NAMES, record_fields

__all__ = [
    "RECORDS",
    "RECORD_NAMES",
    "SCHEMA_ID",
    "SCHEMA_PATH",
    "build_schema",
    "check",
    "dumps_schema",
    "record_fields",
    "write_schema",
]
