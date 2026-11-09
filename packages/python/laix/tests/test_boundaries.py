"""The decision surface stays independent from the app kit."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import laix
import laix.appkit
import laix.decision

PACKAGE = Path(laix.__file__).resolve().parent
DECISION = PACKAGE / "decision"
DECISION_FILES = sorted((DECISION).rglob("*.py"))
APP_KIT_MODULES = {
    "runtime",
    "records",
    "delivery",
    "platform",
    "layer",
    "bench",
    "appkit",
}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            prefix = "." * node.level
            found.add(prefix + node.module)
            found.update(f"{prefix}{node.module}.{item.name}" for item in node.names)
        elif isinstance(node, ast.Import):
            found.update(item.name for item in node.names)
    return found


def _reaches_app_kit(name: str, modules: set[str]) -> bool:
    if name.startswith(".") and not name.startswith(".."):
        # A single dot only reaches another module inside ``decision`` itself.
        return False
    candidate = name.lstrip(".")
    return any(
        candidate == module
        or candidate.startswith(f"{module}.")
        or f".{module}." in candidate
        for module in modules
    )


def test_decision_files_do_not_import_the_app_kit() -> None:
    for path in DECISION_FILES:
        imports = imported_modules(path)
        offenders = {name for name in imports if _reaches_app_kit(name, APP_KIT_MODULES)}
        assert not offenders, f"{path.name} imports app kit modules: {sorted(offenders)}"


def test_decision_surface_has_no_app_kit_objects() -> None:
    assert not hasattr(laix.decision, "DecisionClient")
    assert not hasattr(laix.decision, "ExecutionBridge")
    assert hasattr(laix.decision, "Signal")
    assert hasattr(laix.decision, "DecisionRequest")
    assert hasattr(laix.decision, "Decision")


def test_app_kit_exposes_the_integration_surface() -> None:
    assert hasattr(laix.appkit, "DecisionClient")
    assert hasattr(laix.appkit, "ExecutionBridge")


def test_versions_are_aligned() -> None:
    assert laix.SCHEMA_VERSION == "0.8.0"
    assert laix.ACTION_POLICY_VERSION == "0.8.0"
    assert laix.decision.SCHEMA_VERSION == "0.8.0"
    assert laix.decision.ACTION_POLICY_VERSION == "0.8.0"


def test_a_decision_only_host_never_loads_the_app_kit() -> None:
    script = """
import sys

import laix
from laix import ActionOption, DecisionRequest, Situation, decide

assert "laix.appkit" not in sys.modules, "importing laix loaded laix.appkit"
assert laix.decide is laix.decision.decide

request = DecisionRequest(
    subject="room-1",
    at="2026-11-02T09:00:00+00:00",
    situation=Situation(id="s-1", at="2026-11-02T09:00:00+00:00", subject="room-1"),
    options=(ActionOption(id="a-1", verb="wait", name="wait"),),
)
assert decide(request)[0].verb == "wait"
assert "laix.appkit" not in sys.modules, "deciding in the decision layer loaded laix.appkit"
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(PACKAGE.parent), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr
