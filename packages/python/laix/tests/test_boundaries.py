"""The core surface stays independent from the app kit."""

from __future__ import annotations

import ast
from pathlib import Path

import laix
import laix.appkit
import laix.core

PACKAGE = Path(laix.__file__).resolve().parent
CORE_FILES = [
    PACKAGE / "contracts.py",
    PACKAGE / "decisions.py",
    PACKAGE / "outcome.py",
    PACKAGE / "evaluation.py",
    PACKAGE / "schema.py",
    PACKAGE / "core" / "__init__.py",
    *sorted((PACKAGE / "policies").glob("*.py")),
]
APP_KIT_MODULES = {
    "attention",
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
            found.add(node.module)
            found.update(f"{node.module}.{item.name}" for item in node.names)
        elif isinstance(node, ast.Import):
            found.update(item.name for item in node.names)
    return found


def test_core_files_do_not_import_the_app_kit() -> None:
    for path in CORE_FILES:
        imports = imported_modules(path)
        offenders = {
            name
            for name in imports
            for module in APP_KIT_MODULES
            if name == module or name.startswith(f"{module}.") or f".{module}." in name
        }
        assert not offenders, f"{path.name} imports app kit modules: {sorted(offenders)}"


def test_core_surface_has_no_app_kit_objects() -> None:
    assert not hasattr(laix.core, "Layer")
    assert not hasattr(laix.core, "Signal")
    assert not hasattr(laix.core, "ExecutionBridge")
    assert hasattr(laix.core, "DecisionRequest")
    assert hasattr(laix.core, "PolicyDecision")


def test_app_kit_exposes_the_integration_surface() -> None:
    assert hasattr(laix.appkit, "Layer")
    assert hasattr(laix.appkit, "Signal")
    assert hasattr(laix.appkit, "ExecutionBridge")
    assert hasattr(laix.appkit, "run_bench")


def test_versions_are_aligned() -> None:
    assert laix.SCHEMA_VERSION == "0.6.1"
    assert laix.POLICY_VERSION == "0.6.1"
    assert laix.core.SCHEMA_VERSION == "0.6.1"
    assert laix.core.POLICY_VERSION == "0.6.1"
