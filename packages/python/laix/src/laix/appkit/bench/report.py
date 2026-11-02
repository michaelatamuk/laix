"""The report a bench run returns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .row import BenchRow

FIELDS: tuple[str, ...] = ("verb", "reason_code", "action_id", "requires_approval")


@dataclass(frozen=True, slots=True)
class BenchReport:
    rows: tuple[BenchRow, ...]
    fields: tuple[str, ...] = FIELDS

    @property
    def total(self) -> int:
        return len(self.rows)

    @property
    def passed(self) -> int:
        return sum(1 for row in self.rows if row.passed)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def agreement(self) -> float:
        return round(self.passed / self.total, 4) if self.total else 1.0

    def by_suite(self) -> dict[str, dict[str, Any]]:
        names = []
        for row in self.rows:
            if row.suite not in names:
                names.append(row.suite)
        result: dict[str, dict[str, Any]] = {}
        for name in names:
            rows = [row for row in self.rows if row.suite == name]
            passed = sum(1 for row in rows if row.passed)
            result[name] = {
                "cases": len(rows),
                "passed": passed,
                "failed": len(rows) - passed,
                "agreement": round(passed / len(rows), 4) if rows else 1.0,
            }
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "agreement": self.agreement,
            "fields": list(self.fields),
            "suites": self.by_suite(),
            "rows": [
                {
                    "suite": row.suite,
                    "case": row.case,
                    "passed": row.passed,
                    "mismatches": list(row.mismatches),
                    "expected": dict(row.expected),
                    "actual": dict(row.actual),
                }
                for row in self.rows
            ],
        }


__all__ = ["FIELDS", "BenchReport"]
