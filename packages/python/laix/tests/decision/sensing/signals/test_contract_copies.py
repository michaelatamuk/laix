"""The canonical contracts and the packaged copies stay identical."""

from __future__ import annotations

import json
from pathlib import Path

import laix.decision.sensing.signals as attention_pkg
import laix.decision.evaluation.cases as evaluation_pkg

PACKAGES = Path(__file__).resolve().parents[6]
CANONICAL = PACKAGES / "contracts"
PACKAGED = Path(attention_pkg.__file__).resolve().parent
PACKAGED_BENCH = Path(evaluation_pkg.__file__).resolve().parent


def test_attention_vectors_are_in_sync() -> None:
    canonical = json.loads((CANONICAL / "signal-attention.v1.json").read_text(encoding="utf-8"))
    packaged = json.loads((PACKAGED / "signal-attention.v1.json").read_text(encoding="utf-8"))
    assert packaged == canonical


def test_attention_bench_is_in_sync() -> None:
    canonical = json.loads((CANONICAL / "signal-attention-bench.v1.json").read_text(encoding="utf-8"))
    packaged = json.loads((PACKAGED_BENCH / "signal-attention-bench.v1.json").read_text(encoding="utf-8"))
    assert packaged == canonical
