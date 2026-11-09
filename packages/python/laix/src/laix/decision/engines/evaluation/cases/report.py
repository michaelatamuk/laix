"""The report a parity run returns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .row import Row


@dataclass(frozen=True, slots=True)
class Report:
    rows: tuple[Row, ...] = ()
    fields: tuple[str, ...] = ("verb", "reason_code", "deliver", "record", "requires_approval")

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
    def agreement_rate(self) -> float:
        return round(self.passed / self.total, 4) if self.total else 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cases": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "agreementRate": self.agreement_rate,
            "fields": list(self.fields),
            "rows": [
                {
                    "case": row.case_id,
                    "passed": row.passed,
                    "mismatches": list(row.mismatches),
                    "expected": [dict(item) for item in row.expected],
                    "actual": [dict(item) for item in row.actual],
                }
                for row in self.rows
            ],
        }


__all__ = ["Report"]
