"""LAIX-Bench: ten suites, one report, a CLI."""

from __future__ import annotations

import json

from laix.appkit.bench import main, run_bench, suite_names


def test_bench_runs_every_decision_class() -> None:
    report = run_bench()
    assert report.total == 25
    assert report.passed == 25
    assert report.failed == 0
    assert report.agreement == 1.0
    assert len(report.by_suite()) == 10


def test_bench_lists_each_suite() -> None:
    names = suite_names()
    assert len(names) == 10
    assert "attention" in names
    assert "verification" in names
    assert "escalation" in names


def test_bench_can_run_one_suite() -> None:
    report = run_bench(["safety"])
    assert report.total == 2
    assert report.agreement == 1.0
    assert set(report.by_suite()) == {"safety"}


def test_bench_report_is_serialisable() -> None:
    document = run_bench().to_dict()
    assert document["total"] == 25
    assert document["agreement"] == 1.0
    assert len(document["rows"]) == 25


def test_bench_cli_json(capsys) -> None:
    assert main(["--json"]) == 0
    document = json.loads(capsys.readouterr().out)
    assert document["passed"] == 25


def test_bench_cli_can_fail_under(capsys) -> None:
    assert main(["--fail-under", "1.1"]) == 1
    capsys.readouterr()
