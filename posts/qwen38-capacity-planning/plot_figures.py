#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "matplotlib==3.10.5",
# ]
# ///
"""Generate the Qwen3.8 capacity-planning figures from capacity-data.json."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT = Path(__file__).resolve().parent
DATA = json.loads((OUT / "capacity-data.json").read_text(encoding="utf-8"))
PROFILE_DATA = json.loads(
    (OUT / "short-profile-data.json").read_text(encoding="utf-8")
)
SHARED_SHORT = json.loads(
    (OUT / "shared12k-short-data.json").read_text(encoding="utf-8")
)
SHARED_REFERENCE = json.loads(
    (OUT / "shared12k-reference-data.json").read_text(encoding="utf-8")
)

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
            "Creator": "posts/qwen38-capacity-planning/plot_figures.py",
            "Date": "2026-08-22",
        },
    )
    plt.close(fig)

    source = path.read_text(encoding="utf-8")
    title_id = re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-") + "-title"
    desc_id = title_id.replace("-title", "-desc")
    source = source.replace(
        "<svg ", f'<svg role="img" aria-labelledby="{title_id} {desc_id}" ', 1
    )
    marker = source.find(">", source.find("<svg")) + 1
    accessibility = (
        f'\n  <title id="{title_id}">{html.escape(title)}</title>'
        f'\n  <desc id="{desc_id}">{html.escape(description)}</desc>'
    )
    path.write_text(source[:marker] + accessibility + source[marker:], encoding="utf-8")


def clean_axes(ax, *, grid_axis: str = "y") -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_linewidth(1.8)
    ax.grid(axis=grid_axis, color=GRID, linewidth=1.0, alpha=0.9)
    ax.set_axisbelow(True)


def ttft_p95_s(trial: dict) -> float:
    return trial["ttft_ms"]["p95"] / 1000


def boundary_trials() -> None:
    title = "Each workload has a repeated adjacent pass and fail boundary"
    description = (
        "Three panels show three independent cold-cache p95 time-to-first-token "
        "measurements at the maximum passing concurrency and the next integer for "
        "2K-input 512-output, 8K-input 1K-output, and 16K-input 2K-output workloads. "
        "All passing trials are below the ten-second line and all failing trials are above it."
    )
    colors = [CYAN, VIOLET, ORANGE]
    with plt.xkcd(scale=0.62, length=100, randomness=2), style():
        fig, axes = plt.subplots(1, 3, figsize=(13, 5.7), dpi=160, sharey=True)
        fig.suptitle("one SLO, three different concurrency boundaries", x=0.04, ha="left")
        for ax, workload, color in zip(axes, DATA["workloads"], colors):
            pass_c = workload["maximum_passing_concurrency"]
            fail_c = workload["first_failing_concurrency"]
            pass_y = [ttft_p95_s(t) for t in workload["passing_trials"]]
            fail_y = [ttft_p95_s(t) for t in workload["failing_trials"]]
            offsets = [-0.055, 0.0, 0.055]
            ax.scatter(
                [pass_c + value for value in offsets], pass_y, s=95,
                color=MINT, edgecolor=INK, linewidth=1.3, zorder=4, label="pass"
            )
            ax.scatter(
                [fail_c + value for value in offsets], fail_y, s=95, marker="X",
                color=PINK, edgecolor=INK, linewidth=1.2, zorder=4, label="fail"
            )
            ax.plot([pass_c, fail_c], [sum(pass_y) / 3, sum(fail_y) / 3],
                    color=color, linewidth=2.5, linestyle="--", zorder=2)
            ax.axhline(10, color=INK, linewidth=2, linestyle=":")
            ax.set_xticks([pass_c, fail_c], [f"C={pass_c}", f"C={fail_c}"])
            ax.set_ylim(6.3, 14.1)
            ax.set_title(workload["label"], fontsize=14)
            clean_axes(ax)
            ax.text(0.04, 0.95, f"max = {pass_c}", transform=ax.transAxes,
                    va="top", fontweight="bold", color=color)
        axes[0].set_ylabel("p95 time to first token, seconds")
        axes[-1].text(0.98, 10.15, "10 s SLO", ha="right", va="bottom",
                      color=INK, fontsize=10, fontweight="bold",
                      transform=axes[-1].get_yaxis_transform())
        axes[0].legend(frameon=False, loc="lower left")
        fig.subplots_adjust(top=0.78, wspace=0.15)
        finish(fig, "boundary-trials.svg", title, description)


def throughput_vs_slo() -> None:
    title = "Output throughput overlaps after the first-token SLO fails"
    description = (
        "Six 8K-input and 1K-output trials plot aggregate output tokens per second "
        "against p95 time to first token. Concurrency-seven and concurrency-eight "
        "throughput overlaps, but all concurrency-eight points sit above the ten-second SLO."
    )
    workload = next(item for item in DATA["workloads"] if item["configured_isl"] == 8192)
    with plt.xkcd(scale=0.65, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(11.7, 6.2), dpi=160)
        for key, marker, color, label in (
            ("passing_trials", "o", MINT, f'C={workload["maximum_passing_concurrency"]} pass'),
            ("failing_trials", "X", PINK, f'C={workload["first_failing_concurrency"]} fail'),
        ):
            trials = workload[key]
            ax.scatter(
                [trial["output_throughput_tps"] for trial in trials],
                [ttft_p95_s(trial) for trial in trials],
                s=130, marker=marker, color=color, edgecolor=INK, linewidth=1.4,
                label=label, zorder=4,
            )
            for index, trial in enumerate(trials, 1):
                ax.annotate(str(index),
                            (trial["output_throughput_tps"], ttft_p95_s(trial)),
                            xytext=(7, 5), textcoords="offset points", fontsize=9)
        ax.axhline(10, color=INK, linewidth=2.2, linestyle=":")
        ax.text(204.5, 10.12, "10 s TTFT SLO", va="bottom", fontweight="bold")
        ax.set_xlim(203.5, 223)
        ax.set_ylim(8.35, 10.95)
        ax.set_xlabel("aggregate output throughput, tok/s")
        ax.set_ylabel("p95 time to first token, seconds")
        ax.set_title("output throughput overlaps while p95 TTFT crosses the SLO", loc="left")
        clean_axes(ax, grid_axis="both")
        ax.legend(frameon=False, loc="lower right")
        ax.text(0.01, 0.02, "numbers beside points are independent trial IDs",
                transform=ax.transAxes, color=MUTED, fontsize=9.5)
        finish(fig, "throughput-vs-slo.svg", title, description)


def capacity_envelope() -> None:
    title = "Maximum concurrency falls as requests grow longer"
    description = (
        "Horizontal bars show maximum passing closed-loop concurrency under p95 TTFT "
        "below ten seconds: eleven for 2K input and 512 output, seven for 8K and 1K, "
        "and five for 16K and 2K. All values are from three independent confirmations."
    )
    workloads = DATA["workloads"]
    values = [item["maximum_passing_concurrency"] for item in workloads]
    labels = [item["label"] for item in workloads]
    colors = [CYAN, VIOLET, ORANGE]
    with plt.xkcd(scale=0.65, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(11.5, 5.8), dpi=160)
        bars = ax.barh(range(3), values, color=colors, edgecolor=INK, linewidth=1.8,
                       height=0.62)
        ax.set_yticks(range(3), labels)
        ax.invert_yaxis()
        ax.set_xlim(0, 12.6)
        ax.set_xticks(range(0, 13, 2))
        ax.set_xlabel("maximum closed-loop concurrency")
        ax.set_title("capacity depends on the request size", loc="left")
        clean_axes(ax, grid_axis="x")
        for bar, value in zip(bars, values):
            ax.text(value - 0.35, bar.get_y() + bar.get_height() / 2, str(value),
                    va="center", ha="right", fontsize=18, fontweight="bold", color=INK)
            ax.text(value + 0.2, bar.get_y() + bar.get_height() / 2,
                    f"C={value + 1} fails", va="center", fontsize=10.5, color=PINK)
        ax.text(0.99, 0.03, "4 x B70 | Qwen3.8-27B MTP | p95 TTFT < 10 s",
                transform=ax.transAxes, ha="right", color=MUTED, fontsize=9.5)
        finish(fig, "capacity-envelope.svg", title, description)


def profile_shaping() -> None:
    title = "Recurrent-state capacity and decode graphs change short-request concurrency"
    description = (
        "The left panel shows the highest tested passing concurrency for the same "
        "2K-input and 512-output workload. Lowering only the server maximum context "
        "from 262K to 8K leaves the confirmed boundary at eleven. Increasing the "
        "recurrent-state entry pool with matching decode graph batches produces "
        "passing steps at sixteen and twenty. With maximum context at 8K, the final "
        "passing concurrency is twenty-three; with maximum context at 12K, it is "
        "twenty-two. The right panel shows all three 12K C=22 p95 TTFT trials below "
        "ten seconds and the mixed C=23 trials."
    )
    cells = {cell["label"]: cell for cell in PROFILE_DATA["cells"]}
    steps = [
        ("262K\n48 entries\ngraph 8", "native256k-m48-g8-c11", 11, "C=11 max"),
        ("8K\n48 entries\ngraph 8", "ctx8k-m48-g8-c11", 11, "C=11 max"),
        ("8K\n80 entries\ngraph 16", "ctx8k-m80-g16-c16", 16, "C≥16"),
        ("8K\n120 entries\ngraph 24", "ctx8k-m120-g24-c20", 20, "C≥20"),
        ("8K\n128 entries\ngraph 25", "ctx8k-m128-g25-c23", 23, "C=23"),
        ("12K\n128 entries\ngraph 25", None, 22, "C=22"),
    ]
    colors = [YELLOW, CYAN, VIOLET, ORANGE, PINK, MINT]
    with plt.xkcd(scale=0.62, length=100, randomness=2), style():
        fig, (left, right) = plt.subplots(
            1, 2, figsize=(14.6, 6.1), dpi=160,
            gridspec_kw={"width_ratios": [1.8, 1]},
        )
        bars = left.bar(
            range(len(steps)), [step[2] for step in steps], color=colors,
            edgecolor=INK, linewidth=1.7, width=0.68,
        )
        left.set_xticks(range(len(steps)), [step[0] for step in steps])
        left.tick_params(axis="x", labelsize=8.7)
        left.set_xlabel(
            "maximum context / recurrent-state entries / largest decode graph batch",
            fontsize=9.5,
        )
        left.set_ylim(0, 27)
        left.set_ylabel("highest tested passing concurrency")
        left.set_title("short-workload server configurations", loc="left", fontsize=15)
        clean_axes(left)
        for bar, step in zip(bars, steps):
            left.text(
                bar.get_x() + bar.get_width() / 2, step[2] + 0.55, step[3],
                ha="center", fontsize=10.5, fontweight="bold",
            )
        left.annotate(
            "lower maximum context only:\nno capacity change",
            xy=(1, 11), xytext=(0.45, 18.3),
            arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 1.6},
            ha="center", color=INK, fontsize=10,
        )
        left.text(
            0.02, 0.97, "C≥16 and C≥20 were intermediate passing tests",
            transform=left.transAxes, va="top", color=MUTED, fontsize=9.2,
            bbox={"facecolor": PAPER, "edgecolor": "none", "pad": 1.5},
        )

        final_cells = SHARED_SHORT["cells"]
        for x, cell in enumerate(final_cells):
            for offset, trial in zip((-0.08, 0, 0.08), cell["trials"]):
                passed = trial["strict_slo_pass"]
                right.scatter(
                    x + offset, ttft_p95_s(trial), s=115,
                    marker="o" if passed else "X",
                    color=MINT if passed else PINK,
                    edgecolor=INK, linewidth=1.35, zorder=4,
                )
        right.axhline(10, color=INK, linewidth=2.1, linestyle=":")
        right.text(1.25, 10.04, "10 s SLO", va="bottom", ha="right",
                   fontsize=9.5, fontweight="bold")
        right.set_xticks([0, 1], ["C=22\n3 pass", "C=23\n2 pass, 1 fail"])
        right.set_xlim(-0.35, 1.35)
        right.set_ylim(8.8, 11.15)
        right.set_ylabel("p95 time to first token, seconds")
        right.set_title("adjacent pass and fail trials", loc="left", fontsize=15)
        clean_axes(right)
        fig.suptitle(
            "recurrent-state capacity limits the short workload",
            x=0.055, ha="left", fontsize=19, fontweight="bold",
        )
        fig.subplots_adjust(top=0.82, wspace=0.32)
        finish(fig, "profile-shaping.svg", title, description)


def model_state_map() -> None:
    title = "Attention pages and recurrent state grow along different axes"
    description = (
        "A schematic follows one request through Qwen3.8. Full-attention layers add "
        "token-indexed KV pages, while Gated DeltaNet layers retain a fixed recurrent "
        "state per active sequence. Decode graph capture supplies fast paths for listed batch sizes "
        "but does not allocate request slots or reduce long-prompt prefill work."
    )
    with plt.xkcd(scale=0.55, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(12.4, 6.2), dpi=160)
        ax.set_xlim(0, 12.4)
        ax.set_ylim(0, 6.2)
        ax.axis("off")
        ax.set_title("one request allocates token pages and recurrent state", loc="left")

        prompt = FancyBboxPatch((0.25, 2.25), 2.15, 1.35,
                                boxstyle="round,pad=0.06,rounding_size=0.08",
                                facecolor=YELLOW, edgecolor=INK, linewidth=2)
        ax.add_patch(prompt)
        ax.text(1.325, 3.08, "one sequence", ha="center", fontweight="bold", fontsize=14)
        ax.text(1.325, 2.62, "prompt + output", ha="center", fontsize=10.5)

        branches = [
            (3.4, 3.55, 3.55, 1.55, CYAN, "16 full-attention layers",
             "KV pages grow with tokens", "max-total-tokens"),
            (3.4, 1.15, 3.55, 1.55, MINT, "48 Gated DeltaNet layers",
             "fixed state per active request", "max-mamba-cache-size"),
        ]
        for x, y, w, h, color, heading, body, flag in branches:
            patch = FancyBboxPatch((x, y), w, h,
                                   boxstyle="round,pad=0.06,rounding_size=0.08",
                                   facecolor=color, edgecolor=INK, linewidth=2)
            ax.add_patch(patch)
            ax.text(x + w / 2, y + 1.08, heading, ha="center", fontweight="bold", fontsize=12)
            ax.text(x + w / 2, y + 0.66, body, ha="center", fontsize=10.2)
            ax.text(x + w / 2, y + 0.25, flag, ha="center", fontsize=9.4,
                    family="monospace")
            ax.add_patch(FancyArrowPatch((2.42, 2.92), (x - 0.08, y + h / 2),
                                         arrowstyle="-|>", mutation_scale=15,
                                         linewidth=1.8, color=INK))

        graph = FancyBboxPatch((8.15, 2.25), 3.75, 1.35,
                               boxstyle="round,pad=0.06,rounding_size=0.08",
                               facecolor=VIOLET, edgecolor=INK, linewidth=2)
        ax.add_patch(graph)
        ax.text(10.025, 3.08, "decode graph replay", ha="center", fontweight="bold", fontsize=13)
        ax.text(10.025, 2.62, "compiled fast paths for named batches", ha="center", fontsize=10.3)
        ax.add_patch(FancyArrowPatch((6.98, 4.3), (8.08, 3.38), arrowstyle="-|>",
                                     mutation_scale=15, linewidth=1.8, color=INK))
        ax.add_patch(FancyArrowPatch((6.98, 1.9), (8.08, 2.48), arrowstyle="-|>",
                                     mutation_scale=15, linewidth=1.8, color=INK))
        ax.text(10.05, 1.73, "graphs speed execution; they do not set the active-request limit",
                ha="center", color=MUTED, fontsize=10)
        ax.text(0.3, 0.28,
                "schematic: color separates resource classes; box area carries no quantity",
                color=MUTED, fontsize=9.5)
        finish(fig, "model-state-map.svg", title, description)


def shared_profile() -> None:
    title = "The tuned configuration raises 2K/512 from 11 to 22 and leaves 8K/1K at 7"
    description = (
        "Grouped bars compare the native configuration, with 262K maximum context, "
        "48 recurrent-state entries, and a largest captured decode batch of eight, against "
        "the tuned configuration, with 12K maximum context, 128 recurrent-state "
        "entries, and a largest captured batch of twenty-five. The 2K-input 512-output "
        "workload rises from eleven to twenty-two, while the 8K-input 1K-output "
        "workload stays at seven."
    )
    labels = ["2K / 512", "8K / 1K"]
    native = [11, 7]
    shared = [22, 7]
    with plt.xkcd(scale=0.6, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(11.8, 6.2), dpi=160)
        x = [0, 1]
        width = 0.34
        left = ax.bar([v - width / 2 for v in x], native, width, color=CYAN,
                      edgecolor=INK, linewidth=1.8,
                      label="native: context 262K | state 48 | max graph 8")
        right = ax.bar([v + width / 2 for v in x], shared, width, color=MINT,
                       edgecolor=INK, linewidth=1.8, hatch="//",
                       label="tuned: context 12K | state 128 | max graph 25")
        ax.set_xticks(x, labels)
        ax.set_ylabel("maximum passing concurrency")
        ax.set_ylim(0, 25)
        ax.set_title("the tuned configuration changes 2K / 512, not 8K / 1K", loc="left")
        clean_axes(ax)
        for bars in (left, right):
            for bar in bars:
                value = int(bar.get_height())
                ax.text(bar.get_x() + bar.get_width() / 2, value + 0.5, f"C={value}",
                        ha="center", fontweight="bold", fontsize=12)
        ax.legend(frameon=False, loc="upper right")
        finish(fig, "shared-profile.svg", title, description)


def matched_reference() -> None:
    title = "The native and tuned configurations give the same 8K-input limit"
    description = (
        "Four groups show three p95 time-to-first-token trials each for the 8K-input "
        "1K-output workload. The native 262K-context configuration and tuned "
        "12K-context configuration both pass concurrency seven near 8.7 seconds "
        "and fail concurrency eight near 10.67 seconds, with the ten-second SLO marked."
    )
    native_workload = next(item for item in DATA["workloads"] if item["configured_isl"] == 8192)
    groups = [
        ("native config\nC=7", native_workload["passing_trials"]),
        ("native config\nC=8", native_workload["failing_trials"]),
        ("tuned 12K config\nC=7", SHARED_REFERENCE["cells"][0]["trials"]),
        ("tuned 12K config\nC=8", SHARED_REFERENCE["cells"][1]["trials"]),
    ]
    with plt.xkcd(scale=0.58, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(11.8, 6.1), dpi=160)
        for x, (label, trials) in enumerate(groups):
            passed = "C=7" in label
            values = [ttft_p95_s(t) for t in trials]
            for offset, value in zip((-0.07, 0, 0.07), values):
                ax.scatter(x + offset, value, s=120, marker="o" if passed else "X",
                           color=MINT if passed else PINK, edgecolor=INK,
                           linewidth=1.35, zorder=4)
            ax.plot([x - 0.12, x + 0.12], [sum(values) / 3] * 2,
                    color=INK, linewidth=2)
        ax.axhline(10, color=INK, linewidth=2.1, linestyle=":")
        ax.text(3.42, 10.04, "10 s SLO", ha="right", va="bottom", fontweight="bold")
        ax.set_xticks(range(4), [g[0] for g in groups])
        ax.set_ylabel("p95 time to first token, seconds")
        ax.set_ylim(8.2, 11.15)
        ax.set_title("8K / 1K reaches the TTFT limit before state capacity", loc="left")
        clean_axes(ax)
        ax.text(0.01, 0.02, "each marker is an independent 64-request cold-cache trial",
                transform=ax.transAxes, color=MUTED, fontsize=9.5)
        finish(fig, "matched-reference.svg", title, description)


def protocol() -> None:
    title = "AIPerf search and confirmation protocol for a latency SLO"
    description = (
        "A left-to-right flow fixes the serving identity and workload, finds the range "
        "between passing and failing concurrency, confirms the adjacent integers three "
        "times from cold cache, then validates raw generated text and server token usage."
    )
    boxes = [
        ("fix the test", "image, model,\nrequest size, SLO", YELLOW),
        ("find the range", "large steps, then\nadjacent integers", CYAN),
        ("confirm", "3 x pass and\n3 x next fail", VIOLET),
        ("validate output", "raw SSE +\nserver usage", MINT),
    ]
    with plt.xkcd(scale=0.6, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(12, 4.8), dpi=160)
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 4.8)
        ax.axis("off")
        ax.set_title("from latency SLO to measured concurrency", loc="left")
        for index, (label, detail, color) in enumerate(boxes):
            x = 0.35 + index * 3.0
            patch = FancyBboxPatch(
                (x, 1.45), 2.35, 1.65, boxstyle="round,pad=0.08,rounding_size=0.12",
                facecolor=color, edgecolor=INK, linewidth=2,
            )
            ax.add_patch(patch)
            ax.text(x + 1.175, 2.55, label, ha="center", va="center",
                    fontsize=13, fontweight="bold")
            ax.text(x + 1.175, 1.92, detail, ha="center", va="center",
                    fontsize=10.8, color=INK)
            ax.text(x + 0.15, 3.35, str(index + 1), fontsize=14, fontweight="bold")
            if index < len(boxes) - 1:
                arrow = FancyArrowPatch(
                    (x + 2.38, 2.28), (x + 2.93, 2.28), arrowstyle="-|>",
                    mutation_scale=15, linewidth=2, color=INK,
                )
                ax.add_patch(arrow)
        ax.text(0.4, 0.55,
                "report maximum C only when latency and generation correctness pass together",
                fontsize=11.5, fontweight="bold")
        finish(fig, "capacity-protocol.svg", title, description)


def social_card() -> None:
    title = "Qwen3.8 capacity on the native and tuned server configurations"
    description = (
        "Social card comparing the same 2K-input and 512-output workload on four "
        "Intel Arc Pro B70 GPUs: concurrency eleven on the native configuration, "
        "with 262K context, 48 recurrent-state entries, and a largest graph batch of "
        "eight; and concurrency twenty-two on the tuned configuration, with 12K "
        "context, 128 entries, and a largest graph batch of twenty-five. Both serve "
        "seven concurrent 8K-input 1K-output requests."
    )
    values = [11, 22]
    labels = [
        "native config\ncontext 262K | state 48 | max graph 8",
        "tuned 12K config\ncontext 12K | state 128 | max graph 25",
    ]
    colors = [CYAN, MINT]
    with plt.xkcd(scale=0.55, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(12, 6.3), dpi=100)
        bars = ax.bar(range(2), values, color=colors, edgecolor=INK, linewidth=2,
                      width=0.58)
        clean_axes(ax)
        ax.set_xticks(range(2), labels)
        ax.set_ylabel("maximum concurrency")
        ax.set_ylim(0, 27)
        ax.set_title("Qwen3.8 capacity on four B70s", loc="left", fontsize=24)
        ax.text(0.01, 0.91, "2K / 512 | p95 first token < 10 s | 8K / 1K remains C=7 on both",
                transform=ax.transAxes, color=MUTED, fontsize=12)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.45, f"C={value}",
                    ha="center", fontsize=17, fontweight="bold")
        finish(fig, "card.svg", title, description, pad=0.1)


if __name__ == "__main__":
    boundary_trials()
    throughput_vs_slo()
    capacity_envelope()
    model_state_map()
    profile_shaping()
    shared_profile()
    matched_reference()
    protocol()
    social_card()
