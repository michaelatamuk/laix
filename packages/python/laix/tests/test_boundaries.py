"""The core surface stays independent from the app kit."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import laix
import laix.appkit
import laix.core

PACKAGE = Path(laix.__file__).resolve().parent
CORE = PACKAGE / "core"
CORE_FILES = sorted((CORE).rglob("*.py"))
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
        # A single dot only reaches another module inside ``core`` itself.
        return False
    candidate = name.lstrip(".")
    return any(
        candidate == module
        or candidate.startswith(f"{module}.")
        or f".{module}." in candidate
        for module in modules
    )


def test_core_files_do_not_import_the_app_kit() -> None:
    for path in CORE_FILES:
        imports = imported_modules(path)
        offenders = {name for name in imports if _reaches_app_kit(name, APP_KIT_MODULES)}
        assert not offenders, f"{path.name} imports app kit modules: {sorted(offenders)}"


def test_core_surface_has_no_app_kit_objects() -> None:
    assert not hasattr(laix.core, "Layer")
    assert not hasattr(laix.core, "ExecutionBridge")
    assert hasattr(laix.core, "Signal")
    assert hasattr(laix.core, "DecisionRequest")
    assert hasattr(laix.core, "Decision")


def test_app_kit_exposes_the_integration_surface() -> None:
    assert hasattr(laix.appkit, "Layer")
    assert hasattr(laix.appkit, "ExecutionBridge")


def test_versions_are_aligned() -> None:
    assert laix.SCHEMA_VERSION == "0.8.0"
    assert laix.ACTION_POLICY_VERSION == "0.8.0"
    assert laix.core.SCHEMA_VERSION == "0.8.0"
    assert laix.core.ACTION_POLICY_VERSION == "0.8.0"


def test_a_core_only_host_never_loads_the_app_kit() -> None:
    script = """
import sys

import laix.core
from laix.core import ActionOption, DecisionRequest, Situation, decide

assert "laix.appkit" not in sys.modules, "importing laix.core loaded laix.appkit"

request = DecisionRequest(
    subject="room-1",
    at="2026-11-02T09:00:00+00:00",
    situation=Situation(id="s-1", at="2026-11-02T09:00:00+00:00", subject="room-1"),
    options=(ActionOption(id="a-1", verb="wait", name="wait"),),
)
assert decide(request)[0].verb == "wait"
assert "laix.appkit" not in sys.modules, "deciding in core loaded laix.appkit"
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
