"""Every example must run and print a result."""

from __future__ import annotations

import contextlib
import io
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
PYTHON_EXAMPLES = sorted((ROOT / "examples" / "python").rglob("*.py"))
APP_EXAMPLES = sorted((ROOT / "examples" / "apps").glob("*.py"))
EXAMPLES = PYTHON_EXAMPLES + APP_EXAMPLES


@pytest.mark.parametrize(
    "path",
    EXAMPLES,
    ids=lambda item: item.relative_to(ROOT / "examples").as_posix(),
)
def test_example_runs_and_prints(path: Path) -> None:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        runpy.run_path(str(path), run_name="__main__")
    assert output.getvalue().strip(), f"{path.name} printed nothing"
