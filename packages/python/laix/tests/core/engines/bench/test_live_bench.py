"""The training-free live decision benchmark."""

from __future__ import annotations

from laix import UtilityPlanner, default_cases, default_planners, run_live_bench


def _row(report, case: str, planner: str):
    return next(
        row for row in report.rows if row.case == case and row.planner == planner
    )


def test_benchmark_covers_every_case_and_planner() -> None:
    report = run_live_bench()

    assert len(report.cases) == len(default_cases())
    assert len(report.planners) == len(default_planners())
    assert len(report.rows) == len(report.cases) * len(report.planners)
    assert all(0.0 <= item.accuracy <= 1.0 for item in report.metrics)


def test_commitment_planner_wins_the_commitment_case() -> None:
    report = run_live_bench()

    assert _row(report, "commitment", "commitment").correct is True
    assert _row(report, "commitment", "utility").correct is False


def test_human_attention_planner_wins_the_attention_case() -> None:
    report = run_live_bench()

    assert _row(report, "attention", "attention").correct is True
    assert _row(report, "attention", "utility").correct is False


def test_execution_planner_wins_execution_cases() -> None:
    report = run_live_bench()

    for case in ("irreversible", "unknown", "approval"):
        assert _row(report, case, "execution").correct is True, case
        assert _row(report, case, "utility").correct is False, case


def test_benefit_baseline_breaks_a_hard_limit() -> None:
    report = run_live_bench()
    metrics = {item.planner: item for item in report.metrics}

    assert metrics["benefit"].safety_violations >= 1


def test_report_serializes_and_prints() -> None:
    report = run_live_bench()
    payload = report.to_dict()

    assert set(payload) == {"cases", "planners", "rows", "metrics"}
    assert "accuracy" in report.summary()
    assert isinstance(payload["rows"][0]["latency_ms"], float)


def test_custom_case_and_planner() -> None:
    case = default_cases()[0]
    report = run_live_bench([case], {"utility": UtilityPlanner()})

    assert report.cases == (case.name,)
    assert report.planners == ("utility",)
    assert len(report.rows) == 1
    assert report.metrics[0].decisions == 1
