"""The versioned record set the schema describes.

One class per owning module; this file only names the set.
"""

from __future__ import annotations

from dataclasses import fields

from ..decisions import (
    ActionOption,
    Belief,
    Constraint,
    Decision,
    Goal,
    Observation,
    Receipt,
    Situation,
    Trace,
)
from ..outcome import Outcome

RECORDS = (
    Observation,
    Belief,
    Goal,
    Constraint,
    ActionOption,
    Situation,
    Outcome,
    Receipt,
    Trace,
    Decision,
)

RECORD_NAMES = tuple(item.__name__ for item in RECORDS)


def record_fields(record: type) -> list[str]:
    return [item.name for item in fields(record)]


__all__ = ["RECORDS", "RECORD_NAMES", "record_fields"]
