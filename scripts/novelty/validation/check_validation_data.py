"""Preflight a validation JSONL file before analysis."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = ROOT / "data" / "incident-replay" / "output" / "anonymised.jsonl"
PII_KEYS = {
    "full_name",
    "first_name",
    "last_name",
    "email",
    "phone",
    "address",
    "customer_id",
    "customer_name",
    "account_id",
    "user_id",
    "ip",
    "ip_address",
}
PII_PATTERN = re.compile(r"(email|phone|address|account|user|customer|ssn)", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    return parser.parse_args()


def pii_keys(value: Any, path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}" if path else key
            if key in PII_KEYS or PII_PATTERN.search(key):
                found.append(child)
            found.extend(pii_keys(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(pii_keys(item, f"{path}[{index}]"))
    return found


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        print(f"missing input: {args.input}")
        print("Start from data/incident-replay/README.md and the collection kit.")
        return 2

    rows = [
        json.loads(line)
        for line in args.input.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    errors: list[str] = []
    pii: list[str] = []
    ids: set[str] = set()
    actions: Counter[str] = Counter()
    option_counts: Counter[int] = Counter()

    for number, row in enumerate(rows, 1):
        label = f"line {number}"
        for key in ("id", "at", "subject", "options", "human_action"):
            if key not in row:
                errors.append(f"{label}: missing {key}")
        if "id" in row:
            if str(row["id"]) in ids:
                errors.append(f"{label}: duplicate id {row['id']}")
            ids.add(str(row["id"]))
        if "at" in row:
            try:
                datetime.fromisoformat(str(row["at"]))
            except ValueError:
                errors.append(f"{label}: invalid ISO-8601 time {row['at']!r}")
        options = row.get("options")
        if not isinstance(options, list) or len(options) < 2:
            errors.append(f"{label}: needs at least two options")
            continue
        option_ids = {str(option.get("id")) for option in options if isinstance(option, dict)}
        option_counts[len(options)] += 1
        for option in options:
            if not isinstance(option, dict):
                errors.append(f"{label}: option is not an object")
                continue
            for key in ("id", "verb", "name"):
                if key not in option:
                    errors.append(f"{label}: option missing {key}")
        if str(row.get("human_action")) not in option_ids:
            errors.append(f"{label}: human_action is not an option id")
        actions[str(row.get("human_action"))] += 1
        pii.extend(f"{label}: {key}" for key in pii_keys(row))

    print(f"file: {args.input}")
    print(f"rows: {len(rows)}")
    print(f"unique ids: {len(ids)}")
    print(f"options per case: {dict(sorted(option_counts.items()))}")
    print(f"human actions: {dict(actions.most_common())}")
    if pii:
        print(f"PII-like keys: {len(pii)}")
        for item in pii[:10]:
            print(f"  - {item}")
    if errors:
        print(f"errors: {len(errors)}")
        for item in errors[:20]:
            print(f"  - {item}")
        return 1
    print("OK: validation data is ready for analysis")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
