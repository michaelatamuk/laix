"""Export the standalone decision schema and the reason-code registry.

Run from the repository root:

    python scripts/contracts/export_contracts.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "packages" / "python" / "laix" / "src"
CONTRACTS = ROOT / "packages" / "contracts"
sys.path.insert(0, str(SRC))

from laix.decision.contract.reason_codes import reason_code_registry  # noqa: E402
from laix.decision.schema import build_schema  # noqa: E402


def decision_schema() -> dict:
    definition = build_schema()["$defs"]["Decision"]
    definition["title"] = "LAIX Decision v1"
    definition["description"] = (
        "The public decision shape returned by decide, DecisionClient and every policy."
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://laix.dev/contracts/decision.v1.schema.json",
        **definition,
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    CONTRACTS.mkdir(parents=True, exist_ok=True)
    write_json(CONTRACTS / "decision.v1.schema.json", decision_schema())
    write_json(CONTRACTS / "reason-codes.v1.json", reason_code_registry())
    print("wrote packages/contracts/decision.v1.schema.json")
    print("wrote packages/contracts/reason-codes.v1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
