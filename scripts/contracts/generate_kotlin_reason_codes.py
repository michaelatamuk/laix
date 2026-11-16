"""Generate the Kotlin reason-code registry from the published contract.

Run from the repository root after editing ``packages/contracts/reason-codes.v1.json``:

    python scripts/contracts/generate_kotlin_reason_codes.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "packages/contracts/reason-codes.v1.json"
TARGET = (
    ROOT
    / "packages/kotlin/laix/src/main/kotlin/dev/laix/decision/contract/ReasonCodes.kt"
)

HEADER = '''/**
 * Generated from packages/contracts/reason-codes.v1.json. Do not edit by hand.
 */

package dev.laix.decision.contract

import dev.laix.decision.contracts.SCHEMA_VERSION

object ReasonCodes {
    const val VERSION: String = "__VERSION__"

    const val NOTE: String =
        "__NOTE__"

    val SIGNAL_ATTENTION: List<String> = listOf(
__SIGNAL_ATTENTION__
    )

    val PLANNER: List<String> = listOf(
__PLANNER__
    )

    val POLICY: List<String> = listOf(
__POLICY__
    )

    val APPKIT: List<String> = listOf(
__APPKIT__
    )

    val BENCH: List<String> = listOf(
__BENCH__
    )

    val GROUPS: Map<String, List<String>> = linkedMapOf(
        "signal_attention" to SIGNAL_ATTENTION,
        "planner" to PLANNER,
        "policy" to POLICY,
        "appkit" to APPKIT,
        "bench" to BENCH,
    )

    val CODES: List<String> = GROUPS.values.flatten().distinct().sorted()

    fun registry(): Map<String, Any> = linkedMapOf(
        "version" to VERSION,
        "schema_version" to SCHEMA_VERSION,
        "extensible" to true,
        "note" to NOTE,
        "groups" to GROUPS,
        "codes" to CODES,
    )
}
'''


def items(codes: list[str]) -> str:
    return "\n".join(f'        "{code}",' for code in codes)


def main() -> int:
    contract = json.loads(SOURCE.read_text(encoding="utf-8"))
    groups = contract["groups"]
    text = HEADER
    replacements = {
        "__VERSION__": contract["version"],
        "__NOTE__": contract["note"].replace('"', '\\"'),
        "__SIGNAL_ATTENTION__": items(groups["signal_attention"]),
        "__PLANNER__": items(groups["planner"]),
        "__POLICY__": items(groups["policy"]),
        "__APPKIT__": items(groups["appkit"]),
        "__BENCH__": items(groups["bench"]),
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
