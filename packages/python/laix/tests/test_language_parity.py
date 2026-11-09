"""The Python and TypeScript packages must expose the same verbs."""

from __future__ import annotations

import re
from pathlib import Path

import laix

ROOT = Path(__file__).resolve().parents[3]
TS_CONTRACTS = ROOT / "typescript" / "laix" / "src" / "decision" / "contracts.ts"


def test_typescript_verb_list_matches_python() -> None:
    source = TS_CONTRACTS.read_text(encoding="utf-8")
    match = re.search(r"export const VERBS:\s*Verb\[\]\s*=\s*\[(.*?)\];", source, re.S)
    assert match, "TypeScript VERBS array not found"
    verbs = tuple(re.findall(r'"([a-z]+)"', match.group(1)))
    assert verbs == laix.VERBS
