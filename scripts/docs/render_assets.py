"""Render the README and social assets from the LAIX brand source.

Development-only. Requires Pillow and matplotlib:

    python -m pip install -r scripts/docs/requirements-assets.txt
    python scripts/docs/render_assets.py

The source cover is committed at ``docs/assets/source/laix-cover.png`` so the
outputs are reproducible without the external slide deck.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "assets"
SOURCE = ASSETS / "source" / "laix-cover.png"
RESULTS = ROOT / "results" / "live-decision-benchmark" / "metrics" / "summary.json"
ABLATIONS = ROOT / "results" / "live-decision-benchmark" / "ablations" / "results.json"
FONT_DIR = Path("C:/Windows/Fonts")

SCALE = 2

BG = "#050A18"
BG_2 = "#0B1220"
SURFACE = "#0E1830"
SURFACE_2 = "#111C33"
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
TEAL = "#2DD4BF"
BLUE = "#3B82F6"
PURPLE = "#A855F7"
AMBER = "#F59E0B"


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def rgba(value: str, alpha: int) -> tuple[int, int, int, int]:
    return (*rgb(value), alpha)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def gradient(size: tuple[int, int], top: str, bottom: str) -> Image.Image:
    _width, height = size
    column = Image.new("RGB", (1, height))
    start = rgb(top)
    end = rgb(bottom)
    for y in range(height):
        ratio = y / max(1, height - 1)
        column.putpixel(
            (0, y),
            tuple(int(a + (b - a) * ratio) for a, b in zip(start, end)),
        )
    return column.resize(size)


def glow(
    image: Image.Image,
    center: tuple[int, int],
    radius: int,
    color: str,
    alpha: int,
    blur: int,
) -> None:
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x, y = center
    draw.ellipse(
        [x - radius, y - radius, x + radius, y + radius],
        fill=rgba(color, alpha),
    )
    image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))


def spaced_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    face: ImageFont.FreeTypeFont,
    fill: str,
    spacing: int,
) -> None:
    x, y = xy
    for character in text:
        draw.text((x, y), character, font=face, fill=fill)
        x += draw.textlength(character, font=face) + spacing


def wrap(
    draw: ImageDraw.ImageDraw,
    text: str,
    face: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=face) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def rounded_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    outline: str,
    width: int = 3,
    radius: int = 28,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str,
    width: int = 5,
) -> None:
    draw.line([start, end], fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    head = 18
    left = (
        end[0] - head * math.cos(angle - math.pi / 7),
        end[1] - head * math.sin(angle - math.pi / 7),
    )
    right = (
        end[0] - head * math.cos(angle + math.pi / 7),
        end[1] - head * math.sin(angle + math.pi / 7),
    )
    draw.polygon([end, left, right], fill=color)


def cover_layer(size: tuple[int, int]) -> Image.Image:
    cover = Image.open(SOURCE).convert("RGBA")
    cover = cover.resize(size, Image.LANCZOS)
    fade_width = int(size[0] * 0.28)
    fade = Image.new("RGBA", size, (0, 0, 0, 0))
    fade_draw = ImageDraw.Draw(fade)
    for x in range(fade_width):
        ratio = 1 - x / fade_width
        alpha = int(255 * ratio**1.8)
        fade_draw.line([(x, 0), (x, size[1])], fill=rgba(BG, alpha))
    return Image.alpha_composite(cover, fade)


def render_logo() -> None:
    cover = Image.open(SOURCE).convert("RGB")
    cover = cover.resize((512, 512), Image.LANCZOS)
    cover.save(ASSETS / "logo.png", optimize=True)

    # A square avatar crops the mark only.
    source = Image.open(SOURCE).convert("RGB")
    avatar = source.crop((200, 0, 1000, 800)).resize((512, 512), Image.LANCZOS)
    avatar.save(ASSETS / "avatar.png", optimize=True)


def render_banner() -> None:
    width, height = 1280 * SCALE, 640 * SCALE
    canvas = gradient((width, height), BG, BG_2).convert("RGBA")
    glow(canvas, (2250, 620), 620, TEAL, 24, 220)
    glow(canvas, (1900, 300), 420, BLUE, 18, 240)

    cover_size = (500 * SCALE, 500 * SCALE)
    cover_x = width - cover_size[0] - 60 * SCALE
    cover_y = 70 * SCALE
    cover = cover_layer(cover_size)
    mask = Image.new("L", cover_size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, cover_size[0], cover_size[1]], radius=28 * SCALE, fill=255
    )
    cover.putalpha(mask)
    canvas.alpha_composite(cover, (cover_x, cover_y))

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [cover_x, cover_y, cover_x + cover_size[0], cover_y + cover_size[1]],
        radius=28 * SCALE,
        outline="#1E293B",
        width=2 * SCALE,
    )
    left = 90 * SCALE
    draw.line(
        [(left, 90 * SCALE), (left + 64 * SCALE, 90 * SCALE)],
        fill=TEAL,
        width=6 * SCALE,
    )
    spaced_text(
        draw,
        (left, 118 * SCALE),
        "LIVE DECISION RUNTIME",
        font("seguisb.ttf", 22 * SCALE),
        TEAL,
        6 * SCALE,
    )

    headline_font = font("segoeuib.ttf", 52 * SCALE)
    headline_lines = ["The live decision runtime", "for AI agents and", "automations"]
    y = 190 * SCALE
    for line in headline_lines:
        draw.text((left, y), line, font=headline_font, fill=TEXT)
        y += 72 * SCALE

    body_font = font("segoeui.ttf", 26 * SCALE)
    body = (
        "Act, ask, wait, verify or escalate - with one contract "
        "and a reason for every move."
    )
    body_y = 450 * SCALE
    for line in wrap(draw, body, body_font, 600 * SCALE):
        draw.text((left, body_y), line, font=body_font, fill=MUTED)
        body_y += 36 * SCALE

    footer_font = font("seguisb.ttf", 21 * SCALE)
    footer_y = 580 * SCALE
    items = ["Training-free", "Decision continuity", "Auditable"]
    x = left
    for index, item in enumerate(items):
        draw.text((x, footer_y), item, font=footer_font, fill=TEXT)
        x += draw.textlength(item, font=footer_font) + 16 * SCALE
        if index < len(items) - 1:
            draw.ellipse(
                [x, footer_y + 9 * SCALE, x + 7 * SCALE, footer_y + 16 * SCALE],
                fill=TEAL,
            )
            x += 24 * SCALE

    canvas.convert("RGB").resize((1280, 640), Image.LANCZOS).save(
        ASSETS / "banner.png", optimize=True
    )


def render_architecture() -> None:
    width, height = 1600 * SCALE, 900 * SCALE
    canvas = gradient((width, height), BG, BG_2).convert("RGBA")
    glow(canvas, (1600, 180), 700, TEAL, 18, 260)
    glow(canvas, (2500, 1000), 600, PURPLE, 14, 260)

    draw = ImageDraw.Draw(canvas)
    mark = Image.open(ASSETS / "avatar.png").convert("RGBA")
    mark = mark.resize((92 * SCALE, 92 * SCALE), Image.LANCZOS)
    canvas.alpha_composite(mark, (120, 84))

    draw.text(
        (238 * SCALE, 82 * SCALE),
        "One decision contract",
        font=font("segoeuib.ttf", 64 * SCALE),
        fill=TEXT,
    )
    draw.text(
        (238 * SCALE, 166 * SCALE),
        "LAIX sits between planning and execution",
        font=font("segoeui.ttf", 30 * SCALE),
        fill=MUTED,
    )

    panel_y = 240 * SCALE
    panel_w = 320 * SCALE
    panel_h = 300 * SCALE
    gap = 40 * SCALE
    positions = [80 * SCALE + index * (panel_w + gap) for index in range(4)]
    panels = [
        (
            "AGENT / AUTOMATION",
            "Plans the task",
            ["signals  -  options  -  constraints", "host owns the experience"],
            BLUE,
        ),
        (
            "LAIX",
            "Decides the next move",
            [
                "one contract",
                "utility - commitments",
                "execution risk - attention",
                "training-free",
            ],
            TEAL,
        ),
        (
            "HOST",
            "Executes the choice",
            [
                "act  -  ask  -  wait",
                "verify  -  escalate",
                "receipts - idempotency",
            ],
            AMBER,
        ),
        (
            "OUTCOME",
            "Closes the loop",
            ["receipts - outcomes", "calibration", "next decision"],
            PURPLE,
        ),
    ]

    for index, (eyebrow, title, lines, accent) in enumerate(panels):
        x = positions[index]
        fill = SURFACE_2 if index == 1 else SURFACE
        outline = accent if index == 1 else "#1E293B"
        rounded_panel(
            draw,
            (x, panel_y, x + panel_w, panel_y + panel_h),
            fill,
            outline,
            width=4 if index == 1 else 2,
        )
        draw.text(
            (x + 44 * SCALE, panel_y + 42 * SCALE),
            eyebrow,
            font=font("seguisb.ttf", 16 * SCALE),
            fill=accent,
        )
        draw.text(
            (x + 32 * SCALE, panel_y + 88 * SCALE),
            title,
            font=font("segoeuib.ttf", 22 * SCALE),
            fill=TEXT,
        )
        line_y = panel_y + 132 * SCALE
        for line in lines:
            draw.ellipse(
                [
                    x + 32 * SCALE,
                    line_y + 7 * SCALE,
                    x + 40 * SCALE,
                    line_y + 15 * SCALE,
                ],
                fill=accent,
            )
            draw.text(
                (x + 54 * SCALE, line_y),
                line,
                font=font("segoeui.ttf", 14 * SCALE),
                fill=MUTED,
            )
            line_y += 34 * SCALE

    for index in range(3):
        start_x = positions[index] + panel_w + 14 * SCALE
        end_x = positions[index + 1] - 14 * SCALE
        arrow(
            draw,
            (start_x, panel_y + panel_h // 2),
            (end_x, panel_y + panel_h // 2),
            "#334155",
            width=5 * SCALE,
        )

    band_y = 620 * SCALE
    rounded_panel(
        draw,
        (80 * SCALE, band_y, width - 80 * SCALE, band_y + 100 * SCALE),
        SURFACE,
        "#1E293B",
        width=2,
    )
    draw.text(
        (120 * SCALE, band_y + 34 * SCALE),
        "Every decision carries",
        font=font("seguisb.ttf", 22 * SCALE),
        fill=TEXT,
    )
    pill_font = font("seguisb.ttf", 18 * SCALE)
    pills = ["verb", "reason", "confidence", "score", "approval", "trace"]
    x = 120 * SCALE + draw.textlength("Every decision carries", font=font("seguisb.ttf", 22 * SCALE)) + 34 * SCALE
    for pill in pills:
        pill_w = draw.textlength(pill, font=pill_font) + 28 * SCALE
        draw.rounded_rectangle(
            [x, band_y + 22 * SCALE, x + pill_w, band_y + 78 * SCALE],
            radius=24 * SCALE,
            fill=SURFACE,
            outline=TEAL,
            width=2,
        )
        draw.text(
            (x + 14 * SCALE, band_y + 38 * SCALE),
            pill,
            font=pill_font,
            fill=TEAL,
        )
        x += pill_w + 14 * SCALE

    draw.text(
        (width // 2, 790 * SCALE),
        "One contract for utility, commitments, execution risk and human attention.",
        font=font("segoeui.ttf", 20 * SCALE),
        fill=MUTED,
        anchor="mm",
    )
    draw.text(
        (width // 2, 830 * SCALE),
        "Training-free  -  Python + TypeScript  -  Auditable",
        font=font("seguisb.ttf", 18 * SCALE),
        fill=TEAL,
        anchor="mm",
    )
    canvas.convert("RGB").resize((1600, 900), Image.LANCZOS).save(
        ASSETS / "architecture.png", optimize=True
    )


def render_demo_placeholder() -> None:
    width, height = 1200 * SCALE, 675 * SCALE
    canvas = gradient((width, height), BG, BG_2).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    box = (90 * SCALE, 70 * SCALE, width - 90 * SCALE, height - 70 * SCALE)
    draw.rounded_rectangle(
        box,
        radius=28 * SCALE,
        fill=SURFACE,
        outline="#334155",
        width=3 * SCALE,
    )
    draw.text(
        (width // 2, 230 * SCALE),
        "DEMO GIF",
        font=font("segoeuib.ttf", 64 * SCALE),
        fill=TEXT,
        anchor="mm",
    )
    draw.text(
        (width // 2, 330 * SCALE),
        "20-30 seconds  -  1200 x 675  -  under 5 MB",
        font=font("segoeui.ttf", 28 * SCALE),
        fill=MUTED,
        anchor="mm",
    )
    draw.text(
        (width // 2, 420 * SCALE),
        "Record the quickstart or the live-engine example.",
        font=font("segoeui.ttf", 26 * SCALE),
        fill=MUTED,
        anchor="mm",
    )
    command = "python examples/python/03-plan/live_engine.py"
    command_font = font("consola.ttf", 24 * SCALE)
    command_w = draw.textlength(command, font=command_font)
    draw.rounded_rectangle(
        [
            width // 2 - command_w // 2 - 24 * SCALE,
            480 * SCALE,
            width // 2 + command_w // 2 + 24 * SCALE,
            546 * SCALE,
        ],
        radius=10 * SCALE,
        fill=BG,
        outline="#1E293B",
        width=2,
    )
    draw.text(
        (width // 2, 512 * SCALE),
        command,
        font=command_font,
        fill=TEAL,
        anchor="mm",
    )
    draw.text(
        (width // 2, 610 * SCALE),
        "Replace this file with demo.gif when the recording is ready.",
        font=font("segoeui.ttf", 22 * SCALE),
        fill=MUTED,
        anchor="mm",
    )
    canvas.convert("RGB").resize((1200, 675), Image.LANCZOS).save(
        ASSETS / "demo-placeholder.png", optimize=True
    )



PLANNERS = [
    ("live", "LiveDecisionEngine"),
    ("glue", "Glue baseline"),
    ("commitment", "Commitment"),
    ("first", "First / rule"),
    ("attention", "Attention"),
    ("execution", "Execution"),
    ("utility", "Utility"),
    ("benefit", "Benefit"),
]

ABLATIONS_ORDER = [
    ("full", "Full integration"),
    ("equal_weights", "Equal weights"),
    ("no_attention", "No attention"),
    ("no_feasibility_gates", "No feasibility gates"),
    ("no_execution", "No execution"),
    ("no_commitment", "No commitment"),
    ("utility_only", "Utility only"),
]

ACCENT = "#0F766E"
BAR = "#94A3B8"
INK = "#0F172A"
INK_MUTED = "#64748B"
GRID = "#E2E8F0"


def _percent(value: float) -> str:
    return f"{value:.1%}".replace(".0%", "%")


def _style_axes(ax: plt.Axes, title: str, subtitle: str) -> None:
    ax.set_facecolor("white")
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.yaxis.grid(False)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(axis="both", colors=INK_MUTED, labelsize=10, length=0)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.0%}"))
    ax.xaxis.set_major_locator(MultipleLocator(0.2))
    ax.set_xlim(0, 1.14)
    ax.text(
        0.0,
        1.10,
        title,
        transform=ax.transAxes,
        fontsize=13,
        fontweight="bold",
        color=INK,
        va="bottom",
    )
    ax.text(
        0.0,
        1.035,
        subtitle,
        transform=ax.transAxes,
        fontsize=10,
        color=INK_MUTED,
        va="bottom",
    )


def _hbar_panel(
    ax: plt.Axes,
    rows: list[tuple[str, float, list[float]]],
    title: str,
    subtitle: str,
) -> None:
    labels = [label for label, _, _ in rows]
    values = [value for _, value, _ in rows]
    errors = [
        [max(0.0, value - interval[0]) for _, value, interval in rows],
        [max(0.0, interval[1] - value) for _, value, interval in rows],
    ]
    colors = [ACCENT if index == 0 else BAR for index in range(len(rows))]
    ax.barh(
        labels,
        values,
        height=0.62,
        color=colors,
        xerr=errors,
        error_kw={
            "ecolor": INK_MUTED,
            "elinewidth": 1,
            "capsize": 3,
            "capthick": 1,
        },
        zorder=3,
    )
    ax.invert_yaxis()
    for index, (_, value, interval) in enumerate(rows):
        ax.text(
            max(0.03, max(value, interval[1]) + 0.015),
            index,
            f"{_percent(value)}",
            va="center",
            ha="left",
            fontsize=9.5,
            color=INK,
        )
    _style_axes(ax, title, subtitle)


def load_results() -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    summary = json.loads(RESULTS.read_text(encoding="utf-8"))["planners"]
    ablations = json.loads(ABLATIONS.read_text(encoding="utf-8"))["planners"]
    return summary, ablations


def render_benchmark_chart() -> None:
    summary, _ = load_results()
    accuracy = [
        (label, float(summary[key]["accuracy"]), summary[key]["accuracy_ci"])
        for key, label in PLANNERS
    ]
    conflict = [
        (
            label,
            float(summary[key]["conflict_accuracy"]),
            summary[key]["conflict_ci"],
        )
        for key, label in PLANNERS
    ]

    fig, panels = plt.subplots(1, 2, figsize=(12, 5.6), dpi=200)
    fig.patch.set_facecolor("white")
    fig.text(
        0.055,
        0.945,
        "Live decision benchmark",
        fontsize=19,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.055,
        0.9,
        "Frozen 30-case test split · synthetic corpus · higher is better",
        fontsize=10.5,
        color=INK_MUTED,
    )
    _hbar_panel(panels[0], accuracy, "Accuracy", "All 30 cases")
    _hbar_panel(
        panels[1],
        conflict,
        "Conflict accuracy",
        "6 cases where concerns collide",
    )
    fig.subplots_adjust(left=0.155, right=0.975, top=0.76, bottom=0.14, wspace=0.55)
    fig.text(
        0.055,
        0.035,
        "Source: results/live-decision-benchmark/metrics/summary.json · "
        "reproduce: bash scripts/novelty/reproduce.sh",
        fontsize=8,
        color=INK_MUTED,
    )
    fig.savefig(ASSETS / "benchmark.png", facecolor="white")
    plt.close(fig)


def render_ablation_chart() -> None:
    _, ablations = load_results()
    rows = [
        (label, float(ablations[key]["accuracy"]), ablations[key]["accuracy_ci"])
        for key, label in ABLATIONS_ORDER
    ]

    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=200)
    fig.patch.set_facecolor("white")
    fig.text(
        0.055,
        0.945,
        "Ablations",
        fontsize=19,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.055,
        0.9,
        "Accuracy on the frozen 30-case test split · removing one concern at a time",
        fontsize=10.5,
        color=INK_MUTED,
    )
    _hbar_panel(ax, rows, "Accuracy", "Full integration vs removing one concern")
    fig.subplots_adjust(left=0.24, right=0.97, top=0.74, bottom=0.15)
    fig.text(
        0.055,
        0.035,
        "Source: results/live-decision-benchmark/ablations/results.json",
        fontsize=8,
        color=INK_MUTED,
    )
    fig.savefig(ASSETS / "ablation.png", facecolor="white")
    plt.close(fig)


def terminal_frame(command: str, output: str | None = None) -> Image.Image:
    width, height = 1200, 675
    canvas = gradient((width, height), BG, BG_2).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [80, 60, width - 80, height - 60],
        radius=24,
        fill=SURFACE,
        outline="#1E293B",
        width=2,
    )
    draw.rounded_rectangle(
        [80, 60, width - 80, 112],
        radius=24,
        fill=SURFACE_2,
    )
    for index, color in enumerate(("#EF4444", "#F59E0B", "#22C55E")):
        cx = 116 + index * 28
        draw.ellipse([cx - 7, 79, cx + 7, 93], fill=color)
    draw.text(
        (370, 78),
        "live decision runtime",
        font=font("seguisb.ttf", 18),
        fill=MUTED,
    )
    prompt_font = font("consola.ttf", 24)
    draw.text((130, 170), "$", font=prompt_font, fill=TEAL)
    draw.text((162, 170), command, font=prompt_font, fill=TEXT)
    if output:
        draw.text((130, 240), output, font=prompt_font, fill=TEAL)
    return canvas.convert("RGB")


def decision_frame() -> Image.Image:
    width, height = 1200, 675
    canvas = gradient((width, height), BG, BG_2).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (100, 90),
        "One decision",
        font=font("segoeuib.ttf", 52),
        fill=TEXT,
    )
    draw.text(
        (100, 160),
        "The same contract for every move.",
        font=font("segoeui.ttf", 26),
        fill=MUTED,
    )
    rows = [
        ("action", "safe"),
        ("reason", "live_decision"),
        ("promise", "c1 fulfilled"),
        ("contract", "one decision object"),
    ]
    y = 260
    for label, value in rows:
        draw.text((100, y), label, font=font("seguisb.ttf", 24), fill=MUTED)
        draw.text((360, y), value, font=font("consola.ttf", 26), fill=TEAL)
        y += 62
    draw.text(
        (100, 570),
        "act, ask, wait, verify or escalate - with a reason",
        font=font("segoeui.ttf", 22),
        fill=MUTED,
    )
    return canvas.convert("RGB")


def brand_frame() -> Image.Image:
    width, height = 1200, 675
    canvas = gradient((width, height), BG, BG_2).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    mark = Image.open(ASSETS / "avatar.png").convert("RGBA")
    mark = mark.resize((250, 250), Image.LANCZOS)
    canvas.alpha_composite(mark, (100, 200))
    draw.text(
        (390, 250),
        "LAIX",
        font=font("segoeuib.ttf", 76),
        fill=TEXT,
    )
    draw.text(
        (392, 350),
        "The live decision runtime",
        font=font("segoeuib.ttf", 30),
        fill=TEAL,
    )
    draw.text(
        (392, 400),
        "One contract. One decision. A reason for every move.",
        font=font("segoeui.ttf", 22),
        fill=MUTED,
    )
    return canvas.convert("RGB")


def render_demo_gif() -> None:
    command = "python examples/python/03-plan/live_engine.py"
    frames = [
        terminal_frame(command),
        terminal_frame(command, "safe live_decision c1"),
        decision_frame(),
        brand_frame(),
    ]
    palette_frames = [
        frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=128)
        for frame in frames
    ]
    palette_frames[0].save(
        ASSETS / "demo.gif",
        save_all=True,
        append_images=palette_frames[1:],
        duration=[1200, 1600, 2200, 2200],
        loop=0,
        optimize=True,
        disposal=2,
    )


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists():
        raise SystemExit(f"missing brand source: {SOURCE}")
    render_logo()
    render_banner()
    render_architecture()
    render_demo_placeholder()
    render_benchmark_chart()
    render_ablation_chart()
    render_demo_gif()
    print(f"wrote assets to {ASSETS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
