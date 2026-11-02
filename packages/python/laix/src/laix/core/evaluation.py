"""Parity and replay for policies.

Give the harness a list of cases, a decide function and the fields to compare.
It returns a report. This is the shared version of the old app-specific parity
checks: one fixture format, one report, one exit rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Sequence

Decide = Callable[[Any], Sequence[Any]]


@dataclass(frozen=True, slots=True)
class Case:
    id: str
    request: Any
    expected: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class Row:
    case_id: str
    expected: tuple[Mapping[str, Any], ...]
    actual: tuple[Mapping[str, Any], ...]
    mismatches: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.mismatches


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


def _decision_dict(decision: Any) -> dict[str, Any]:
    if isinstance(decision, Mapping):
        return dict(decision)
    to_dict = getattr(decision, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    as_dict = getattr(decision, "as_dict", None)
    if callable(as_dict):
        return dict(as_dict())
    return {
        "verb": getattr(decision, "verb", None),
        "reason_code": getattr(decision, "reason_code", None) or getattr(decision, "reason", None),
        "deliver": getattr(decision, "deliver", True),
        "record": getattr(decision, "record", True),
        "requires_approval": getattr(decision, "requires_approval", False),
    }


def compare(
    cases: Iterable[Case],
    decide: Decide,
    *,
    fields: Iterable[str] = ("verb", "reason_code", "deliver", "record", "requires_approval"),
) -> Report:
    chosen = tuple(fields)
    rows: list[Row] = []
    for case in cases:
        actual = tuple(_decision_dict(item) for item in decide(case.request))
        problems: list[str] = []
        if len(actual) != len(case.expected):
            problems.append(f"decision count {len(actual)} != {len(case.expected)}")
        for index, (want, got) in enumerate(zip(case.expected, actual)):
            for name in chosen:
                if name in want and want[name] != got.get(name):
                    problems.append(f"item {index}: {name} {got.get(name)!r} != {want[name]!r}")
        rows.append(
            Row(
                case_id=case.id,
                expected=tuple(dict(item) for item in case.expected),
                actual=actual,
                mismatches=tuple(problems),
            )
        )
    return Report(rows=tuple(rows), fields=chosen)


def load_cases(document: Mapping[str, Any], *, request_key: str = "request", expected_key: str = "expected") -> tuple[Case, ...]:
    """Read a simple JSON fixture: case -> request + expected decisions."""
    rows: list[Case] = []
    for item in document.get("cases", ()):
        rows.append(
            Case(
                id=str(item.get("id", "?")),
                request=item.get(request_key),
                expected=tuple(dict(value) for value in item.get(expected_key, ())),
            )
        )
    return tuple(rows)


__all__ = ["Case", "Decide", "Report", "Row", "compare", "load_cases"]
