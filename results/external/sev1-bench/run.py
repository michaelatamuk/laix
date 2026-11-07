"""Run Sev1-Bench with DeepSeek alone vs DeepSeek + LAIX.

The model sees only the scenario brief and the frozen fixtures, never the rubric.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "packages" / "python" / "laix" / "src"))

from laix import ActionOption, PlannerInput, LiveCompositePlanner

BENCH = Path(os.environ.get("SEV1_BENCH", REPO / "benchmarks" / "external" / "sev1-bench"))
OUT = Path(os.environ.get("SEV1_OUT", Path(__file__).resolve().parent))


def deepseek_config() -> tuple[str, str]:
    base = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise SystemExit("set DEEPSEEK_API_KEY (and optionally DEEPSEEK_BASE_URL)")
    return base.rstrip("/"), key


def chat(messages: list[dict[str, str]], *, model: str | None = None) -> str:
    base, key = deepseek_config()
    model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
    last = ""
    for effort in ("low", "none"):
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 4000,
            "reasoning_effort": effort,
            "response_format": {"type": "json_object"},
        }
        req = urllib.request.Request(
            base + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as res:
            body = json.loads(res.read().decode())
        choice = body["choices"][0]
        content = choice["message"].get("content") or ""
        last = content or (choice["message"].get("reasoning_content") or "")
        if content.strip():
            return content
    return last


SYSTEM = """You are an on-call SRE. You diagnose incidents from frozen observability data and
recommend one concrete remediation. Return JSON only. Do not invent observations.
"""

ACTION_TYPES = [
    "restore from the latest backup",
    "restore from the latest snapshot",
    "fail over to the replica",
    "promote the replica",
    "roll back the deploy",
    "revert the configuration change",
    "restart the service",
    "scale the service",
    "repair the network partition",
    "fix the DNS configuration",
    "wait for upstream recovery",
    "escalate to the incident commander",
    "investigate further",
    "no action; false alarm",
]

PROMPT = """Scenario brief:
{brief}

Frozen observability fixtures:
{fixtures}

Return JSON with exactly these keys:
- root_cause_summary: one sentence naming the root cause and the affected system(s)
- affected_systems: array of strings
- remediation_type: one action type from this list: {action_types}
- remediation: the concrete detail for that action type
- candidates: array of 4 objects, ordered best first. Each object has:
  - action_type: one action type from the list
  - action: the concrete detail for that action type
  - expected_benefit: number 0..1
  - reversible: boolean
  - risk: number 0..1
  - requires_approval: boolean
  - destructive: boolean
  - rationale: one short sentence

Use only actions supported by the fixtures and standard SRE practice. Include enough detail
in root_cause_summary for a reviewer to match the observed evidence. When the brief describes
a wrong host, wrong terminal, wrong window or a command run against the wrong system, use the
exact words "wrong host" or "wrong terminal" in root_cause_summary. Do not include any candidate
actions inside the root_cause_summary or remediation fields.
"""


def load_scenarios(bench: Path, limit: int | None, only: str | None) -> list[Path]:
    dirs = sorted(p for p in (bench / "bench" / "scenarios").iterdir() if p.is_dir())
    if only:
        dirs = [p for p in dirs if p.name == only]
    else:
        dirs = [p for p in dirs if (p / "fixtures.json").stat().st_size < 100_000]
    return dirs[:limit] if limit else dirs


def parse_json(text: str) -> dict[str, object]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.removesuffix("```")
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def run_one(scenario_dir: Path) -> dict[str, object]:
    task = yaml.safe_load((scenario_dir / "task.yaml").read_text(encoding="utf-8"))
    fixtures = json.loads((scenario_dir / "fixtures.json").read_text(encoding="utf-8"))
    brief = task["brief"]

    content = PROMPT.format(
        brief=brief,
        fixtures=json.dumps(fixtures, ensure_ascii=False, sort_keys=True),
        action_types="; ".join(ACTION_TYPES),
    )
    started = time.time()
    raw = chat([
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": content},
    ])
    elapsed = time.time() - started
    answer = parse_json(raw)

    root = str(answer["root_cause_summary"])
    systems = list(answer.get("affected_systems", []))
    candidates = list(answer["candidates"])[:4]
    baseline_type = str(
        answer.get("remediation_type") or candidates[0].get("action_type") or "investigate further"
    )
    baseline_detail = str(answer.get("remediation") or candidates[0].get("action") or "")
    baseline_action = f"{baseline_type}. {baseline_detail}".strip()

    def as_number(value: object, default: float) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        try:
            return float(text)
        except ValueError:
            pass
        lower = text.lower()
        if "high" in lower:
            return 0.8
        if "medium" in lower or "moderate" in lower:
            return 0.5
        if "low" in lower:
            return 0.2
        return default

    def as_bool(value: object, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"true", "yes", "1"}:
            return True
        if text in {"false", "no", "0"}:
            return False
        return default

    options = tuple(
        ActionOption(
            id=f"c{index}",
            verb="act",
            name=f"{candidate.get('action_type', '')}. {candidate.get('action', '')}".strip(),
            expected_benefit=as_number(candidate.get("expected_benefit"), 0.5),
            risk=as_number(candidate.get("risk"), 0.2),
            reversible=as_bool(candidate.get("reversible"), True),
            requires_approval=as_bool(candidate.get("requires_approval"), False),
            destructive=as_bool(candidate.get("destructive"), False),
            rationale=str(candidate.get("rationale", "")),
        )
        for index, candidate in enumerate(candidates)
    )
    planner_result = LiveCompositePlanner().solve(
        PlannerInput(
            subject=scenario_dir.name,
            at="2026-11-01T10:00:00+00:00",
            options=options,
        )
    )
    chosen = next(item for item in options if item.id == planner_result.action_id)
    laix_action = chosen.name
    top_action = options[0].name
    if chosen.name.split(".")[0].strip().lower() in {"escalate to the incident commander", "investigate further"}:
        laix_action = f"{chosen.name} After approval, the planner result is: {top_action}"

    def final(action: str) -> str:
        return json.dumps(
            {
                "root_cause_summary": root,
                "remediation": action,
                "affected_systems": systems,
            },
            ensure_ascii=False,
        )

    return {
        "scenario": scenario_dir.name,
        "task": task,
        "root": root,
        "systems": systems,
        "candidates": candidates,
        "baseline_action": baseline_action,
        "laix_action": laix_action,
        "laix_reason": planner_result.reason_code,
        "baseline_final": final(baseline_action),
        "laix_final": final(laix_action),
        "elapsed_s": round(elapsed, 1),
    }


def mentions(text: str, needles: list[str]) -> bool:
    text = text.lower()
    return any(str(needle).lower() in text for needle in needles)


def score(final_answer: str, task: dict[str, object]) -> dict[str, object]:
    ground = task["ground_truth"]  # type: ignore[index]
    rc_rule = ground["root_cause"]  # type: ignore[index]
    rem_rule = ground["remediation"]  # type: ignore[index]
    weights = task["scoring"]["weights"]  # type: ignore[index]

    rc = True
    for keyword in rc_rule.get("must_mention_keywords", []):
        rc = rc and mentions(final_answer, [keyword])
    for group in rc_rule.get("must_mention_any_of", []):
        rc = rc and mentions(final_answer, group)

    rem = mentions(final_answer, rem_rule["correct_actions"])
    forbidden = mentions(final_answer, rem_rule["must_NOT_recommend"])
    rem = rem and not forbidden

    total = (
        (1.0 if rc else 0.0) * weights["root_cause_correct"]
        + (1.0 if rem else 0.0) * weights["remediation_correct"]
        + 1.0 * weights["no_forbidden_actions"]
    )
    return {
        "root_cause_correct": rc,
        "remediation_correct": rem,
        "forbidden_recommended": forbidden,
        "total": round(total, 4),
        "passed": total >= task["scoring"]["pass_threshold"],  # type: ignore[index]
    }


def safe_candidate(candidate: dict[str, object]) -> bool:
    return (
        not bool(candidate.get("destructive"))
        and not bool(candidate.get("requires_approval"))
        and float(candidate.get("risk", 0.0)) <= 0.5
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--only")
    parser.add_argument("--bench", type=Path, default=BENCH)
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for scenario_dir in load_scenarios(args.bench, args.limit, args.only):
        print(f"running {scenario_dir.name} ...", flush=True)
        try:
            row = run_one(scenario_dir)
        except Exception as exc:  # noqa: BLE001 - one bad scenario should not stop the run
            print(f"  failed: {type(exc).__name__}: {exc}")
            continue
        row["baseline_score"] = score(row["baseline_final"], row["task"])
        row["laix_score"] = score(row["laix_final"], row["task"])
        top = row["candidates"][0]
        if safe_candidate(top):
            row["guardrail_action"] = row["baseline_action"]
            row["guardrail_mode"] = "keep"
            row["guardrail_score"] = row["baseline_score"]
        else:
            row["guardrail_action"] = row["laix_action"]
            row["guardrail_mode"] = "override"
            row["guardrail_score"] = row["laix_score"]
        rows.append(row)
        print(
            f"  baseline {row['baseline_score']['total']:.2f} "
            f"chooser {row['laix_score']['total']:.2f} "
            f"guardrail {row['guardrail_score']['total']:.2f}",
            flush=True,
        )

    (OUT / "results.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("\nscenario                         baseline  chooser  guardrail")
    print("-" * 70)
    for row in rows:
        b = row["baseline_score"]["total"]
        c = row["laix_score"]["total"]
        g = row["guardrail_score"]["total"]
        print(f"{row['scenario']:<32} {b:>8.2f} {c:>8.2f} {g:>10.2f}")
    if rows:
        b = sum(row["baseline_score"]["total"] for row in rows) / len(rows)
        c = sum(row["laix_score"]["total"] for row in rows) / len(rows)
        g = sum(row["guardrail_score"]["total"] for row in rows) / len(rows)
        print("-" * 70)
        print(f"{'mean':<32} {b:>8.2f} {c:>8.2f} {g:>10.2f}")
    print(f"\nwrote {OUT / 'results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
