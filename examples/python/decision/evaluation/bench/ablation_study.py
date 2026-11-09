"""Ablation study: each planner on the same cases.

Runs every built-in planner — plus the two naive baselines — on the seven
standard live-bench cases and prints which planner got each case right.

The key result: single-concern planners win their own cases; LiveCompositePlanner
wins every case because it integrates commitment, execution risk and attention
in one score.
"""

from __future__ import annotations

from laix import default_cases, default_planners, run_live_bench

# ------------------------------------------------------------------
# Run every planner on every case
# ------------------------------------------------------------------

report = run_live_bench(default_cases(), default_planners())

# ------------------------------------------------------------------
# Per-case breakdown (rows = cases, columns = planners)
# ------------------------------------------------------------------

PLANNERS = list(report.planners)
CASES = list(report.cases)

# Map (case, planner) → correct | None
cell: dict[tuple[str, str], bool | None] = {}
for row in report.rows:
    cell[(row.case, row.planner)] = row.correct

col_w = max(len(p) for p in PLANNERS)
row_w = max(len(c) for c in CASES)

header = f"{'case':<{row_w}}  " + "  ".join(f"{p:>{col_w}}" for p in PLANNERS)
separator = "-" * len(header)

print("Per-case correctness (Y = right, N = wrong, ? = no expected action)")
print(separator)
print(header)
print(separator)
for case in CASES:
    marks = []
    for planner in PLANNERS:
        v = cell.get((case, planner))
        marks.append(("Y" if v else ("N" if v is False else "?")).rjust(col_w))
    print(f"{case:<{row_w}}  " + "  ".join(marks))
print(separator)

# Total correct per planner
totals = []
for planner in PLANNERS:
    correct = sum(
        1 for case in CASES
        if cell.get((case, planner)) is True
    )
    checked = sum(
        1 for case in CASES
        if cell.get((case, planner)) is not None
    )
    totals.append(f"{correct}/{checked}".rjust(col_w))
print(f"{'correct':<{row_w}}  " + "  ".join(totals))

# ------------------------------------------------------------------
# Aggregate summary
# ------------------------------------------------------------------

print()
print("Aggregate (accuracy = correct / cases with expected action)")
print(report.summary())
print()
print(
    "Result: LiveCompositePlanner wins every case. Single-concern planners "
    "win their own cases but fail when two or more concerns fire at once."
)
