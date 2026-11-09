"""Render the two overview diagrams as committed SVGs.

GitHub renders Mermaid natively, but the top-level layer and stage diagrams need
more layout control than block-beta gives. These SVGs are generated from small
data tables so the rows stay symmetric and the styling stays consistent.

Run from the repository root:

    python scripts/docs/render_overview_svgs.py
"""

from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "assets"

FONT = "'Segoe UI', 'Inter', system-ui, sans-serif"
PAGE = "#FFFFFF"
BORDER = "#E2E8F0"
INK = "#0F172A"
MUTED = "#64748B"
RULE = "#F1F5F9"

DECISION_ACCENT = "#0F766E"
DECISION_TINT = "#F0FDFA"
DECISION_STROKE = "#99F6E4"

APPKIT_ACCENT = "#1D4ED8"
APPKIT_TINT = "#EFF6FF"
APPKIT_STROKE = "#BFDBFE"


def _text(
    x: float,
    y: float,
    value: str,
    *,
    size: float = 14,
    weight: int = 400,
    fill: str = INK,
    anchor: str = "start",
    letter_spacing: float | None = None,
    opacity: float | None = None,
) -> str:
    attrs = (
        f'x="{x}" y="{y}" fill="{fill}" font-family="{FONT}" '
        f'font-size="{size}" font-weight="{weight}"'
    )
    if anchor != "start":
        attrs += f' text-anchor="{anchor}"'
    if letter_spacing is not None:
        attrs += f' letter-spacing="{letter_spacing}"'
    if opacity is not None:
        attrs += f' opacity="{opacity}"'
    return f"  <text {attrs}>{html.escape(value)}</text>"


def _rect(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    rx: float = 10,
    fill: str = PAGE,
    stroke: str = BORDER,
    stroke_width: float = 1,
) -> str:
    return (
        f'  <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    )


def _header(
    *,
    title_id: str,
    title: str,
    desc: str,
    eyebrow: str,
    subtitle: str,
    accent: str,
    tint: str,
    stroke: str,
    pill: str,
    height: int,
) -> list[str]:
    return [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" '
            f'viewBox="0 0 1200 {height}" role="img" '
            f'aria-labelledby="{title_id}-title {title_id}-desc">'
        ),
        f'  <title id="{title_id}-title">{html.escape(title)}</title>',
        f'  <desc id="{title_id}-desc">{html.escape(desc)}</desc>',
        _rect(0.5, 0.5, 1199, height - 1, rx=18, fill=PAGE, stroke=BORDER),
        _text(64, 58, eyebrow, size=12, weight=700, fill=accent, letter_spacing=2.5),
        _text(64, 102, title, size=30, weight=700, fill=INK),
        _text(64, 132, subtitle, size=14, fill=MUTED),
        _rect(1016, 40, 120, 30, rx=15, fill=tint, stroke=stroke),
        _text(1076, 59, pill, size=10, weight=700, fill=accent, anchor="middle", letter_spacing=1.5),
        '<line x1="64" y1="150" x2="1136" y2="150" stroke="#F1F5F9" stroke-width="1"/>',
    ]


def _row(
    y: float,
    *,
    index: int,
    label: str,
    cards: tuple[tuple[str, str], ...],
    label_x: float,
    label_width: float,
    card_xs: tuple[float, ...],
    card_width: float,
    height: float,
    accent: str,
    tint: str,
    stroke: str,
    label_dy: float,
    index_dy: float,
    title_dy: float,
    subtitle_dy: float,
    title_size: float,
    subtitle_size: float,
) -> list[str]:
    parts = [
        _rect(label_x, y, label_width, height, fill=tint, stroke=stroke),
        _text(
            label_x + 20,
            y + index_dy,
            f"{index:02d}",
            size=10,
            weight=700,
            fill=accent,
            letter_spacing=1.5,
            opacity=0.75,
        ),
        _text(label_x + 20, y + label_dy, label, size=18, weight=700, fill=accent),
    ]
    for x, (title, subtitle) in zip(card_xs, cards):
        parts.extend(
            [
                _rect(x, y, card_width, height, fill=PAGE, stroke=BORDER),
                _text(x + 22, y + title_dy, title, size=title_size, weight=600, fill=INK),
                _text(x + 22, y + subtitle_dy, subtitle, size=subtitle_size, fill=MUTED),
            ]
        )
    return parts


def _footer(y: float, value: str) -> list[str]:
    return [
        f'  <line x1="64" y1="{y}" x2="1136" y2="{y}" stroke="{RULE}" stroke-width="1"/>',
        _text(64, y + 24, value, size=12.5, fill=MUTED),
    ]


def render_decision() -> str:
    rows = (
        (
            "Contract",
            (
                ("DecisionRequest · Decision", "what crosses the boundary"),
                ("ExecutionReceipt · Trace", "what happened"),
            ),
        ),
        (
            "Domain",
            (
                ("Decisions · Commitments", "what exists and is promised"),
                ("Outcomes · Perception", "what carries forward"),
            ),
        ),
        (
            "Decision",
            (
                ("Single · Sequence · Fleet", "choose one move or a chain"),
                ("History · Explain", "repair and attribute"),
            ),
        ),
        (
            "Sensing",
            (
                ("Signals", "what deserves attention"),
                ("Resources", "what is affordable"),
            ),
        ),
        (
            "Learning",
            (
                ("Calibration · Model", "improve confidence and transitions"),
                ("Bandit · Causal", "learn from outcomes"),
            ),
        ),
        (
            "Evaluation",
            (
                ("Cases · Benchmarks", "fixed evidence"),
                ("Simulation", "counterfactual evidence"),
            ),
        ),
        (
            "Foundation",
            (
                ("Schema", "records and validation"),
                ("Support", "ids · time · values"),
            ),
        ),
    )

    lines = _header(
        title_id="decision",
        title="Seven layers, one decision contract",
        desc=(
            "The seven decision layers: contract, domain, decision, sensing, learning, "
            "evaluation and foundation. The contract is at the top and the foundation at the bottom."
        ),
        eyebrow="DECISION LAYERS",
        subtitle="From what crosses the boundary to what proves the choice.",
        accent=DECISION_ACCENT,
        tint=DECISION_TINT,
        stroke=DECISION_STROKE,
        pill="STATELESS",
        height=800,
    )

    y = 170
    for index, (label, cards) in enumerate(rows, start=1):
        lines.extend(
            _row(
                y,
                index=index,
                label=label,
                cards=cards,
                label_x=64,
                label_width=190,
                card_xs=(268, 709),
                card_width=427,
                height=70,
                accent=DECISION_ACCENT,
                tint=DECISION_TINT,
                stroke=DECISION_STROKE,
                label_dy=48,
                index_dy=24,
                title_dy=30,
                subtitle_dy=51,
                title_size=15.5,
                subtitle_size=12.5,
            )
        )
        y += 80

    lines.extend(
        _footer(
            752,
            "The decision layer is stateless. The host supplies the current state on every request.",
        )
    )
    lines.append("</svg>")
    return "\n".join(lines)


def render_appkit() -> str:
    rows = (
        (
            "Build",
            (
                ("Adapter", "event → request"),
                ("DecisionClient", "one decision"),
                ("Policies", "select · version · shadow"),
            ),
        ),
        (
            "Run",
            (
                ("DecisionRuntime", "observe · decide · measure"),
                ("StreamSession", "event time · revisions"),
                ("LiveContext", "detectors · frames"),
            ),
        ),
        (
            "Execute",
            (
                ("ExecutionBridge", "approve · act · recover"),
                ("Saga", "compensate · recover"),
                ("Proposal · DecisionRecord", "approve · apply · audit"),
            ),
        ),
        (
            "Connect",
            (
                ("Stores", "state · checkpoints · commitments · outcomes"),
                ("Platform", "skills · events · approvals"),
                ("Delivery", "channel · receipt"),
            ),
        ),
        (
            "Operate",
            (
                ("Bench", "cases · suites"),
                ("Metrics", "counters · latency"),
                ("Deployment", "topology · rollout · retention"),
            ),
        ),
    )

    lines = _header(
        title_id="appkit",
        title="Five stages around one decision",
        desc=(
            "The five app-kit stages: build, run, execute, connect and operate. "
            "Each stage wraps the decision with production surfaces."
        ),
        eyebrow="APP KIT",
        subtitle="Build, run, execute, connect and operate the decision in production.",
        accent=APPKIT_ACCENT,
        tint=APPKIT_TINT,
        stroke=APPKIT_STROKE,
        pill="OPTIONAL",
        height=710,
    )

    y = 170
    for index, (label, cards) in enumerate(rows, start=1):
        lines.extend(
            _row(
                y,
                index=index,
                label=label,
                cards=cards,
                label_x=64,
                label_width=170,
                card_xs=(248, 548, 848),
                card_width=288,
                height=82,
                accent=APPKIT_ACCENT,
                tint=APPKIT_TINT,
                stroke=APPKIT_STROKE,
                label_dy=54,
                index_dy=28,
                title_dy=33,
                subtitle_dy=56,
                title_size=15,
                subtitle_size=11,
            )
        )
        y += 94

    lines.extend(
        _footer(
            660,
            "The app kit defines the ports. The host owns execution, data, credentials and transport.",
        )
    )
    lines.append("</svg>")
    return "\n".join(lines)


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "decision-layers.svg").write_text(render_decision(), encoding="utf-8", newline="\n")
    (ASSETS / "appkit-stages.svg").write_text(render_appkit(), encoding="utf-8", newline="\n")
    print("wrote docs/assets/decision-layers.svg and docs/assets/appkit-stages.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
