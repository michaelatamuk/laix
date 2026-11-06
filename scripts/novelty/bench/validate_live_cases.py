"""Validate all live-bench case files against the shared JSON Schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CASES = ROOT / "benchmarks" / "live" / "v1"
SCHEMA = CASES / "schema.json"
SPLITS = ("dev", "test", "adversarial")


def main() -> int:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("jsonschema is required: python -m pip install jsonschema", file=sys.stderr)
        return 2

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    seen: set[str] = set()
    failures = 0

    for split in SPLITS:
        path = CASES / f"{split}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            failures += len(errors)
            print(f"{path.name}: {len(errors)} schema error(s)")
            for error in errors[:5]:
                print(f"  - {error.message}")
        else:
            print(f"{path.name}: valid ({len(payload['cases'])} cases)")
        for case in payload["cases"]:
            case_id = case["id"]
            if case_id in seen:
                failures += 1
                print(f"  - duplicate case id: {case_id}")
            seen.add(case_id)

    if failures:
        print(f"FAIL: {failures} validation error(s)")
        return 1
    print(f"OK: {len(seen)} unique cases are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
