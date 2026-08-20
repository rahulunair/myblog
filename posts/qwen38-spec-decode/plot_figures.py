#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "matplotlib==3.10.5",
# ]
# ///
"""Generate the speculative-decoding article's annotated SVG evidence.

The numeric inputs are copied from the retained test records in the
Qwen3.8-27B project. Diagrams are explicitly schematic.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Rectangle


OUT = Path(__file__).resolve().parent

PAPER = "#fffdf7"
INK = "#243447"
MINT = "#06d6a0"
YELLOW = "#ffc107"
VIOLET = "#8e6cff"
PINK = "#e91e63"
ORANGE = "#ff5722"
CYAN = "#00bcd4"
MUTED = "#6b7785"
GRID = "#d9e2e8"


def style() -> mpl.rc_context:
    return mpl.rc_context(
        {
            "font.family": "URW Bookman",
            "font.size": 12,
            "axes.titleweight": "bold",
            "axes.titlesize": 18,
            "axes.labelsize": 13,
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "svg.fonttype": "none",
            "path.sketch": (1.0, 120.0, 2.0),
        }
    )


def finish(fig, name: str, title: str, description: str, *, pad: float = 0.18) -> None:
    path = OUT / name
    fig.savefig(
        path,
        format="svg",
        bbox_inches="tight",
        pad_inches=pad,
        metadata={
            "Title": title,
            "Description": description,
            "Creator": "posts/qwen38-spec-decode/plot_figures.py",
            "Date": "2026-08-20",
        },
    )
    plt.close(fig)

    source = path.read_text()
    title_id = re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-") + "-title"
    desc_id = title_id.replace("-title", "-desc")
    source = source.replace(
        "<svg ",
        f'<svg role="img" aria-labelledby="{title_id} {desc_id}" ',
        1,
    )
    marker = source.find(">", source.find("<svg")) + 1
    accessibility = (
        f"\n  <title id=\"{title_id}\">{html.escape(title)}</title>"
        f"\n  <desc id=\"{desc_id}\">{html.escape(description)}</desc>"
    )
    path.write_text(source[:marker] + accessibility + source[marker:])


def clean_axes(ax, *, grid_axis="y") -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_linewidth(1.8)
    ax.grid(axis=grid_axis, color=GRID, linewidth=1.0, alpha=0.9)
    ax.set_axisbelow(True)


def box(ax, xy, width, height, label, color, *, sub=None, linewidth=2.0, hatch=None):
    x, y = xy
    rect = Rectangle(
        (x, y), width, height, facecolor=color, edgecolor=INK,
        linewidth=linewidth, hatch=hatch
    )
    ax.add_patch(rect)
    ax.text(x + width / 2, y + height * 0.60, label, ha="center", va="center",
            fontsize=12, fontweight="bold")
    if sub:
        ax.text(x + width / 2, y + height * 0.25, sub, ha="center", va="center",
                fontsize=9.5, color=MUTED)
    return rect


def connect(ax, start, end, label=None, *, color=INK, dashed=False, rad=0.0):
    arrow = FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=14, linewidth=2,
        color=color, linestyle="--" if dashed else "-",
        connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(arrow)
    if label:
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        ax.text(mx, my + 0.16, label, ha="center", va="bottom", fontsize=9.5,
                color=color, bbox={"facecolor": PAPER, "edgecolor": "none", "pad": 1})


def speculative_cycle() -> None:
    title = "One target-controlled speculative decoding iteration"
    description = (
        "A committed prefix enters a cheap draft path, which proposes eight tokens. "
        "The target scores the causal block in one verification pass, the runtime "
        "accepts the matching prefix, commits a target-selected boundary token, and "
        "updates target and draft state before the next iteration. The layout is schematic."
    )
    with plt.xkcd(scale=0.65, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(12, 6.5), dpi=160)
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 7)
        ax.axis("off")
        ax.set_title("one speculative iteration: the target still decides", loc="left", pad=14)

        box(ax, (0.3, 4.8), 2.0, 1.1, "committed prefix", YELLOW, sub="target state is valid")
        box(ax, (3.0, 4.8), 2.0, 1.1, "draft proposal", CYAN, sub="8 candidate positions")
        box(ax, (5.7, 4.8), 2.0, 1.1, "target verify", VIOLET, sub="one causal block")
        box(ax, (8.4, 4.8), 3.0, 1.1, "accept and commit", MINT, sub="matching prefix + boundary")
        connect(ax, (2.3, 5.35), (3.0, 5.35), "cheap path")
        connect(ax, (5.0, 5.35), (5.7, 5.35), "candidate ids")
        connect(ax, (7.7, 5.35), (8.4, 5.35), "target logits")

        tokens = ["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"]
        colors = [MINT, MINT, MINT, MINT, PINK, PAPER, PAPER, PAPER]
        for i, (token, color) in enumerate(zip(tokens, colors)):
            x = 1.0 + i * 1.28
            box(ax, (x, 2.3), 0.86, 0.75, token, color, linewidth=1.5,
                hatch="//" if i >= 5 else None)
            if i < 4:
                ax.text(x + 0.43, 2.08, "accepted", ha="center", fontsize=8.5, color=MUTED)
            elif i == 4:
                ax.text(x + 0.43, 2.08, "first miss", ha="center", fontsize=8.5, color=PINK)
        ax.plot([0.85, 5.92], [1.78, 1.78], color=MINT, linewidth=3)
        ax.text(3.38, 1.42, "four draft tokens survive", ha="center", fontsize=11,
                fontweight="bold", color=INK)
        box(ax, (7.65, 1.55), 2.65, 1.0, "target boundary token", ORANGE,
            sub="becomes next draft anchor")
        connect(ax, (6.85, 2.68), (7.65, 2.05), color=ORANGE)

        ax.text(0.35, 0.45,
                "Speed comes from accepted tokens per cycle. Correctness comes from target verification.",
                fontsize=11.5, fontweight="bold")
        ax.text(11.45, 0.20, "schematic, not to scale", ha="right", fontsize=9, color=MUTED)
        finish(fig, "speculative-cycle.svg", title, description)


def mechanism_paths() -> None:
    title = "MTP and DFlash2 produce the same verify block through different draft paths"
    description = (
        "MTP normalizes one target hidden row and one token embedding, concatenates "
        "them into 10,240 features, projects back to 5,120, runs one auxiliary layer, "
        "and repeats seven times. DFlash2 takes five target-layer features, projects "
        "them into a five-layer sliding-attention backbone once for eight positions, "
        "uses top-16 target-head candidates and a rank-256 local selector, then sends "
        "one eight-token chain to the shared target verifier. The drawing is schematic."
    )
    with plt.xkcd(scale=0.6, length=95, randomness=2), style():
        fig, ax = plt.subplots(figsize=(12, 8.2), dpi=160)
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 9)
        ax.axis("off")
        ax.set_title("same target verifier, very different proposal cost", loc="left", pad=12)

        ax.text(0.35, 7.95, "MTP inside the target checkpoint", fontsize=14, fontweight="bold")
        box(ax, (0.45, 6.55), 1.7, 0.9, "token embed", YELLOW, sub="1 x 5,120")
        box(ax, (2.55, 6.55), 1.7, 0.9, "target hidden", VIOLET, sub="1 x 5,120")
        box(ax, (4.65, 6.55), 1.9, 0.9, "norm + concat", CYAN, sub="1 x 10,240")
        box(ax, (7.0, 6.55), 1.55, 0.9, "fc", ORANGE, sub="back to 5,120")
        box(ax, (9.0, 6.55), 1.75, 0.9, "one aux layer", MINT, sub="next-token logits")
        connect(ax, (2.15, 7.0), (4.65, 7.0))
        connect(ax, (4.25, 7.0), (4.65, 7.0))
        connect(ax, (6.55, 7.0), (7.0, 7.0))
        connect(ax, (8.55, 7.0), (9.0, 7.0))
        connect(ax, (10.75, 7.0), (11.55, 7.0), "repeat 7 times", color=PINK)
        ax.text(11.6, 6.56, "8-token\nchain", ha="center", va="center", fontsize=10,
                fontweight="bold", color=PINK)

        ax.plot([0.35, 11.65], [5.55, 5.55], color=GRID, linewidth=2)
        ax.text(0.35, 4.95, "DFlash2 external draft checkpoint", fontsize=14, fontweight="bold")
        box(ax, (0.45, 3.45), 1.95, 0.95, "target features", VIOLET, sub="layers 5,19,33,47,61")
        box(ax, (2.85, 3.45), 1.65, 0.95, "project", ORANGE, sub="5 x 5,120 to 5,120")
        box(ax, (4.95, 3.45), 2.15, 0.95, "5-layer backbone", CYAN, sub="8 positions in one pass")
        box(ax, (7.55, 3.45), 1.55, 0.95, "target head", YELLOW, sub="top 16 each")
        box(ax, (9.55, 3.45), 2.0, 0.95, "local selector", MINT, sub="rank 256 pair scores")
        connect(ax, (2.4, 3.93), (2.85, 3.93))
        connect(ax, (4.5, 3.93), (4.95, 3.93))
        connect(ax, (7.1, 3.93), (7.55, 3.93))
        connect(ax, (9.1, 3.93), (9.55, 3.93))
        ax.text(6.02, 3.03, "two-tap conv before and after attention and MLP", ha="center",
                fontsize=9.5, color=MUTED)

        box(ax, (4.25, 0.95), 3.5, 1.05, "shared target verification", VIOLET,
            sub="causal score for the proposed 8-token chain")
        connect(ax, (11.45, 6.5), (7.35, 2.0), "MTP chain", color=PINK, rad=0.12)
        connect(ax, (10.55, 3.45), (7.7, 1.65), "DFlash2 chain", color=MINT, rad=-0.08)
        ax.text(11.55, 0.35, "schematic, not to scale", ha="right", fontsize=9, color=MUTED)
        finish(fig, "mtp-vs-dflash2.svg", title, description)


def verify_cliff() -> None:
    title = "The eight-query verification shape caused an XPU attention cliff"
    description = (
        "At 262,144 cached tokens, one query row took 0.505 milliseconds, one "
        "eight-query call took 23.362 milliseconds, eight serial one-query calls "
        "took 3.900 milliseconds, and a batch of eight one-query rows took 2.090 "
        "milliseconds. All measurements used the same 268 megabyte KV scan per row."
    )
    labels = ["1 query", "8 queries\none call", "8 serial\n1-query", "batch of 8\n1-query rows"]
    values = [0.505, 23.362, 3.900, 2.090]
    colors = [YELLOW, PINK, ORANGE, MINT]
    with plt.xkcd(scale=0.65, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(11.5, 6.4), dpi=160)
        bars = ax.bar(range(4), values, width=0.66, color=colors, edgecolor=INK, linewidth=1.8)
        clean_axes(ax)
        ax.set_xticks(range(4), labels)
        ax.set_ylabel("one full-attention layer, ms")
        ax.set_ylim(0, 26)
        ax.set_title("the batched verify shape was 46.3x slower than one query", loc="left")
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.7, f"{value:.3f} ms",
                    ha="center", fontweight="bold")
        ax.annotate("rewrite used this shape", xy=(3, 2.09), xytext=(2.2, 13),
                    arrowprops={"arrowstyle": "-|>", "color": MINT, "lw": 2},
                    color=INK, fontsize=11, fontweight="bold")
        ax.text(0.01, 0.96, "262K cached tokens | TP4 | 268 MB KV scan", transform=ax.transAxes,
                va="top", fontsize=10, color=MUTED)
        finish(fig, "verify-shape-cliff.svg", title, description)


def draft_ring() -> None:
    title = "Opt-in one-million-token DFlash2 physical layout"
    description = (
        "The opt-in one-million-token profile keeps 1,048,576 physical target "
        "token slots. Each of eight DFlash2 state slots receives a private, "
        "page-aligned ring of 2,176 draft slots, derived from a 2,048-token "
        "logical window, page alignment, and an eight-token verify block. The "
        "native 256K profile instead shares the target allocator's physical "
        "indices. The drawing is schematic."
    )
    with plt.xkcd(scale=0.6, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(12, 6.8), dpi=160)
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 7)
        ax.axis("off")
        ax.set_title("the private ring belongs only to the opt-in 1M profile",
                     loc="left", pad=12)

        box(ax, (0.45, 4.8), 11.0, 1.05, "target KV pool: exactly 1,048,576 slots", VIOLET,
            sub="shared by active input and requested output")
        ax.text(0.5, 4.25, "DFlash2 draft KV", fontsize=13.5, fontweight="bold")
        for i in range(8):
            x = 0.5 + i * 1.4
            box(ax, (x, 2.65), 1.05, 0.85, f"ring {i + 1}", MINT if i % 2 == 0 else CYAN,
                sub="2,176", linewidth=1.4)
        ax.text(6.0, 2.05,
                "8 effective requests x 2,176 slots = 17,408 physical draft slots",
                ha="center", fontsize=11.5, fontweight="bold")

        parts = [("2,048 visible", 5.6, YELLOW), ("page guard", 2.3, ORANGE), ("verify 8", 1.5, PINK)]
        left = 1.0
        total = sum(p[1] for p in parts)
        for label, width, color in parts:
            scaled = width / total * 9.8
            box(ax, (left, 0.72), scaled, 0.72, label, color, linewidth=1.3)
            left += scaled
        ax.text(11.45, 0.22, "schematic, not to scale", ha="right", fontsize=9, color=MUTED)
        finish(fig, "dflash2-draft-ring.svg", title, description)


def crossover() -> None:
    title = "Original August 19 sweep before the final graph and lifecycle fixes"
    description = (
        "Original August 19 median streaming decode on four Arc Pro B70 GPUs "
        "with a one-million-token target pool. MTP measured 109.2, 82.3, 50.0, "
        "and 37.2 tokens per second at 32K, 128K, 256K, and 512K input. DFlash2 "
        "measured 71.4, 58.1, 49.1, and 42.2. Each cell is one reported prompt "
        "after one warm-up and predates the final DFlash2 graph and lifecycle fixes."
    )
    x = [32, 128, 256, 512]
    mtp = [109.2, 82.3, 50.0, 37.2]
    dflash = [71.4, 58.1, 49.1, 42.2]
    with plt.xkcd(scale=0.65, length=105, randomness=2), style():
        fig, ax = plt.subplots(figsize=(11.8, 6.6), dpi=160)
        ax.plot(x, mtp, color=MINT, marker="o", markersize=8, linewidth=3, label="MTP")
        ax.plot(x, dflash, color=VIOLET, marker="s", markersize=7, linewidth=3,
                linestyle="--", label="DFlash2")
        clean_axes(ax, grid_axis="both")
        ax.set_xlim(18, 530)
        ax.set_ylim(25, 120)
        ax.set_xticks(x, ["32K", "128K", "256K", "512K"])
        ax.set_xlabel("exact input tokens")
        ax.set_ylabel("median streaming decode, tok/s")
        ax.set_title("August 19 campaign: MTP leads early, DFlash2 at 512K",
                     loc="left")
        for xx, yy in zip(x, mtp):
            ax.text(xx, yy + 4.5, f"{yy:.1f}", ha="center", color=INK, fontsize=10)
        for xx, yy in zip(x, dflash):
            ax.text(xx, yy - 7.0, f"{yy:.1f}", ha="center", color=INK, fontsize=10)
        ax.legend(frameon=False, loc="upper right")
        ax.annotate("within 1.8%", xy=(256, 49.55), xytext=(315, 70),
                    arrowprops={"arrowstyle": "-|>", "color": ORANGE, "lw": 1.8},
                    fontsize=10.5, fontweight="bold")
        ax.text(0.01, 0.02,
                "Aug 19 binary | C=1 | cold radix | 1 warm-up + 1 sample/cell",
                transform=ax.transAxes, color=MUTED, fontsize=9.5)
        finish(fig, "long-context-crossover.svg", title, description)


def short_percentiles() -> None:
    title = "MTP keeps the tighter 16K token-latency tail"
    description = (
        "TPOT percentiles from ten reported prompts after ten warm-ups per arm. At "
        "8K, DFlash2 measured 9.527, 11.973, and 12.714 milliseconds at p50, p90, "
        "and p99, while MTP measured 9.437, 11.836, and 12.464. At 16K, DFlash2 "
        "measured 10.694, 17.607, and 19.201, while MTP measured 9.363, 10.852, "
        "and 11.091 milliseconds."
    )
    groups = ["8K DFlash2", "8K MTP", "16K DFlash2", "16K MTP"]
    vals = [
        (9.527, 11.973, 12.714),
        (9.437, 11.836, 12.464),
        (10.694, 17.607, 19.201),
        (9.363, 10.852, 11.091),
    ]
    colors = [VIOLET, MINT, VIOLET, MINT]
    markers = ["s", "o", "s", "o"]
    with plt.xkcd(scale=0.65, length=105, randomness=2), style():
        fig, ax = plt.subplots(figsize=(11.8, 6.5), dpi=160)
        for i, ((p50, p90, p99), color, marker) in enumerate(zip(vals, colors, markers)):
            ax.plot([i, i], [p50, p99], color=color, linewidth=4, linestyle="--" if i % 2 == 0 else "-")
            ax.scatter([i, i, i], [p50, p90, p99], s=[65, 55, 55], marker=marker,
                       color=[YELLOW, color, PINK], edgecolor=INK, linewidth=1.2, zorder=4)
            ax.text(i + 0.08, p99 + 0.35, f"p99 {p99:.2f}", fontsize=9.5)
        clean_axes(ax)
        ax.set_xticks(range(4), groups)
        ax.set_ylabel("time per output token, ms")
        ax.set_ylim(7, 21.5)
        ax.set_title("the 16K DFlash2 median hides a wider tail", loc="left")
        ax.legend(
            handles=[
                Line2D([0], [0], marker="o", color="none", markerfacecolor=YELLOW,
                       markeredgecolor=INK, label="p50"),
                Line2D([0], [0], marker="o", color="none", markerfacecolor=VIOLET,
                       markeredgecolor=INK, label="p90"),
                Line2D([0], [0], marker="o", color="none", markerfacecolor=PINK,
                       markeredgecolor=INK, label="p99"),
            ], frameon=False, loc="upper left"
        )
        ax.text(0.99, 0.02, "10 measured prompts per arm and shape", transform=ax.transAxes,
                ha="right", fontsize=9.5, color=MUTED)
        finish(fig, "short-tpot-percentiles.svg", title, description)


def phase_split() -> None:
    title = "Target verification owns four fifths of the measured 524K MTP step"
    description = (
        "At a 524,288-token prompt, device timers attributed 36.489 milliseconds "
        "per verify to target verification, 5.125 milliseconds to draft extend, and "
        "3.965 milliseconds to both draft replays. The categorized total was 45.579 "
        "milliseconds and the observed timer step was 46.327 milliseconds."
    )
    labels = ["target verify", "draft extend", "draft replays"]
    values = [36.489, 5.125, 3.965]
    colors = [VIOLET, CYAN, MINT]
    with plt.xkcd(scale=0.65, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(11.6, 5.6), dpi=160)
        left = 0
        for label, value, color in zip(labels, values, colors):
            ax.barh([0], [value], left=[left], height=0.48, color=color,
                    edgecolor=INK, linewidth=1.8, label=label)
            if value > 8:
                ax.text(left + value / 2, 0, f"{value:.3f} ms\n80.1%", ha="center",
                        va="center", fontweight="bold")
            else:
                ax.annotate(f"{label}\n{value:.3f} ms", xy=(left + value / 2, 0.25),
                            xytext=(left + value / 2, 0.73), ha="center", fontsize=9.5,
                            arrowprops={"arrowstyle": "-", "color": INK})
            left += value
        ax.axvline(46.327, color=PINK, linewidth=2.2, linestyle="--")
        ax.text(46.327, -0.47, "observed 46.327 ms", ha="right", color=PINK,
                fontsize=10, fontweight="bold")
        ax.set_xlim(0, 49)
        ax.set_ylim(-0.8, 1.05)
        ax.set_yticks([])
        ax.set_xlabel("milliseconds per speculative verify step")
        ax.set_title("after fixing the draft path, verify became the bottleneck", loc="left")
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.grid(axis="x", color=GRID, linewidth=1)
        ax.set_axisbelow(True)
        ax.text(0.01, 0.02, "23 verify calls | rank 0 | device timers change throughput",
                transform=ax.transAxes, fontsize=9.5, color=MUTED)
        finish(fig, "mtp-524k-phase-split.svg", title, description)


def social_card() -> None:
    title = "MTP and DFlash2 speculative decoding at long context on Arc Pro"
    description = (
        "Social card for the original August 19 sweep, with MTP leading at 32K "
        "and 128K input, the modes meeting at 256K, and DFlash2 leading at 512K "
        "on four Arc Pro B70 GPUs."
    )
    x = [32, 128, 256, 512]
    mtp = [109.2, 82.3, 50.0, 37.2]
    dflash = [71.4, 58.1, 49.1, 42.2]
    with plt.xkcd(scale=0.55, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(12, 6.3), dpi=100)
        ax.plot(x, mtp, color=MINT, marker="o", markersize=8, linewidth=3.2, label="MTP")
        ax.plot(x, dflash, color=VIOLET, marker="s", markersize=7, linewidth=3.2,
                linestyle="--", label="DFlash2")
        clean_axes(ax, grid_axis="both")
        ax.set_xlim(18, 530)
        ax.set_ylim(25, 120)
        ax.set_xticks(x, ["32K", "128K", "256K", "512K"])
        ax.set_ylabel("median decode, tok/s")
        ax.set_title("speculative decoding at 512K on Arc Pro", loc="left", fontsize=24)
        ax.text(0.01, 0.92,
                "original Aug 19 sweep | four B70 GPUs | exact 1M target pool",
                transform=ax.transAxes, fontsize=12, color=MUTED)
        ax.legend(frameon=False, loc="upper right", fontsize=13)
        ax.annotate("crossover", xy=(276, 49.6), xytext=(350, 70),
                    arrowprops={"arrowstyle": "-|>", "color": ORANGE, "lw": 2},
                    fontsize=12, fontweight="bold")
        finish(fig, "card.svg", title, description, pad=0.1)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    speculative_cycle()
    mechanism_paths()
    verify_cliff()
    draft_ring()
    crossover()
    short_percentiles()
    phase_split()
    social_card()
