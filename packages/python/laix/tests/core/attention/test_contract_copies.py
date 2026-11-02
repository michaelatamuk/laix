"""The canonical contracts and the packaged copies stay identical."""

from __future__ import annotations

import json
from pathlib import Path

import laix.core.attention as attention_pkg

PACKAGES = Path(__file__).resolve().parents[5]
CANONICAL = PACKAGES / "contracts"
PACKAGED = Path(attention_pkg.__file__).resolve().parent / "vectors"


def test_attention_vectors_are_in_sync() -> None:
    canonical = json.loads((CANONICAL / "attention.v1.json").read_text(encoding="utf-8"))
    packaged = json.loads((PACKAGED / "attention.v1.json").read_text(encoding="utf-8"))
    assert packaged == canonical


def test_attention_bench_is_in_sync() -> None:
    canonical = json.loads((CANONICAL / "attention-bench.v1.json").read_text(encoding="utf-8"))
    packaged = json.loads((PACKAGED / "bench.v1.json").read_text(encoding="utf-8"))
    assert packaged == canonical
