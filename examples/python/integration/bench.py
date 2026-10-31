"""Run LAIX-Bench from Python.

The result is:

    25 25 1.0

- 25: cases across ten decision classes.
- 25: cases that matched the expected decision.
- 1.0: full agreement.
"""

from laix.bench import run_bench

report = run_bench()
print(report.total, report.passed, report.agreement)
