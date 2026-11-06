"""Anonymise incident exports into validation rows.

Input: JSON Lines. Each line has `id`, `at`, `subject`, `options`, `human_action` and optional
`human_reason`, `outcome`, `context`.

Output: JSON Lines with common PII keys removed recursively.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "data" / "validation" / "anonymised" / "incidents-v1.jsonl"

PII_KEYS = {
    "full_name",
    "first_name",
    "last_name",
    "email",
    "phone",
    "phone_number",
    "address",
    "street",
    "city",
    "postcode",
    "zip",
    "ssn",
    "social_security_number",
    "customer_id",
    "customer_name",
    "account_id",
    "user_id",
    "ip",
    "ip_address",
}
PII_PATTERN = re.compile(r"(email|phone|address|account|user|customer|ssn)", re.IGNORECASE)


def strip_pii(value: Any, *, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {
            item_key: strip_pii(item_value, key=item_key)
            for item_key, item_value in value.items()
            if item_key not in PII_KEYS and not PII_PATTERN.search(item_key)
        }
    if isinstance(value, list):
        return [strip_pii(item) for item in value]
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        print(f"missing input: {args.input}")
        return 2

    rows: list[dict[str, Any]] = []
    skipped = 0
    for number, line in enumerate(args.input.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"line {number}: invalid JSON ({exc}); skipped")
            skipped += 1
            continue

        required = ("id", "at", "subject", "options", "human_action")
        missing = [key for key in required if key not in payload]
        if missing:
            print(f"line {number}: missing {', '.join(missing)}; skipped")
            skipped += 1
            continue

        option_ids = {str(option.get("id")) for option in payload["options"]}
        if str(payload["human_action"]) not in option_ids:
            print(f"line {number}: human_action is not one of the options; skipped")
            skipped += 1
            continue

        clean = strip_pii(payload)
        clean["source"] = "incident"
        rows.append(clean)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    try:
        shown = args.output.relative_to(ROOT)
    except ValueError:
        shown = args.output
    print(f"wrote {len(rows)} rows to {shown}")
    if skipped:
        print(f"skipped {skipped} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
