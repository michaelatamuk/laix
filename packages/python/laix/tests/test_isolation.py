"""Isolation guard: the layer uses only the standard library and its own modules."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import laix

ROOT = Path(laix.__file__).resolve().parent
LOCAL_PACKAGES = {"laix"}

# Optional integrations are allowed to import their extra only when the user
# installs it. The core stays dependency-free.
OPTIONAL_IMPORTS = {
    "appkit/mcp_server.py": {"mcp"},
}


def _python_files(root: Path):
    for path in sorted(root.rglob("*.py")):
        if "tests" in path.parts:
            continue
        yield path


def external_imports(root: Path) -> list[str]:
    hits: list[str] = []
    for path in _python_files(root):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(root).as_posix()
        allowed = OPTIONAL_IMPORTS.get(relative, set())
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules = [node.module.split(".")[0]]
            for module in modules:
                if (
                    module not in sys.stdlib_module_names
                    and module not in LOCAL_PACKAGES
                    and module not in allowed
                ):
                    hits.append(f"{path.name}: {module}")
    return hits


def test_package_uses_only_the_standard_library() -> None:
    assert external_imports(ROOT) == []


def test_guard_detects_a_third_party_import(tmp_path: Path) -> None:
    package = tmp_path / "laix"
    package.mkdir()
    (package / "bad.py").write_text("import fastapi\nimport numpy\n", encoding="utf-8")
    hits = external_imports(package)
    assert any("fastapi" in hit for hit in hits)
    assert any("numpy" in hit for hit in hits)


def test_no_adapter_is_inside_the_layer() -> None:
    assert not (ROOT / "adapter").exists()
    assert not (ROOT / "adapters").exists()
