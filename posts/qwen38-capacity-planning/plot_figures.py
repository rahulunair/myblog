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
            "Date": "2026-08-21",
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
        ax.set_title("the decoder stayed busy while admission latency failed", loc="left")
        clean_axes(ax, grid_axis="both")
        ax.legend(frameon=False, loc="lower right")
        ax.text(0.01, 0.02, "numbers beside points are independent trial IDs",
                transform=ax.transAxes, color=MUTED, fontsize=9.5)
        finish(fig, "throughput-vs-slo.svg", title, description)


def capacity_envelope() -> None:
    title = "Maximum concurrency falls as the request shape grows"
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
        ax.set_title("capacity belongs to the workload row", loc="left")
        clean_axes(ax, grid_axis="x")
        for bar, value in zip(bars, values):
            ax.text(value - 0.35, bar.get_y() + bar.get_height() / 2, str(value),
                    va="center", ha="right", fontsize=18, fontweight="bold", color=INK)
            ax.text(value + 0.2, bar.get_y() + bar.get_height() / 2,
                    f"C={value + 1} fails", va="center", fontsize=10.5, color=PINK)
        ax.text(0.99, 0.03, "4 x B70 | Qwen3.8-27B MTP | p95 TTFT < 10 s",
                transform=ax.transAxes, ha="right", color=MUTED, fontsize=9.5)
        finish(fig, "capacity-envelope.svg", title, description)


def protocol() -> None:
    title = "A four-stage protocol turns a latency SLO into a capacity limit"
    description = (
        "A left-to-right flow pins the serving identity and workload, locates a cheap "
        "concurrency neighborhood, confirms the adjacent pass and fail points three "
        "times from cold cache, then validates raw generated text and server token usage."
    )
    boxes = [
        ("pin the row", "digest, model,\nshape, SLO", YELLOW),
        ("locate", "exponential +\nbisection", CYAN),
        ("confirm", "3 x pass and\n3 x next fail", VIOLET),
        ("prove work", "raw SSE +\nserver usage", MINT),
    ]
    with plt.xkcd(scale=0.6, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(12, 4.8), dpi=160)
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 4.8)
        ax.axis("off")
        ax.set_title("from a service contract to a number I can defend", loc="left")
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
                    fontsize=10, color=INK)
            ax.text(x + 0.15, 3.35, str(index + 1), fontsize=14, fontweight="bold")
            if index < len(boxes) - 1:
                arrow = FancyArrowPatch(
                    (x + 2.38, 2.28), (x + 2.93, 2.28), arrowstyle="-|>",
                    mutation_scale=15, linewidth=2, color=INK,
                )
                ax.add_patch(arrow)
        ax.text(0.4, 0.55,
                "publish Cmax only when latency and generation correctness pass together",
                fontsize=11.5, fontweight="bold")
        finish(fig, "capacity-protocol.svg", title, description)


def social_card() -> None:
    title = "Qwen3.8 capacity under a ten-second first-token SLO"
    description = (
        "Social card showing maximum closed-loop concurrency of eleven, seven, and five "
        "for short, reference, and heavy request shapes on four Intel Arc Pro B70 GPUs."
    )
    workloads = DATA["workloads"]
    values = [item["maximum_passing_concurrency"] for item in workloads]
    labels = ["2K / 512", "8K / 1K", "16K / 2K"]
    colors = [CYAN, VIOLET, ORANGE]
    with plt.xkcd(scale=0.55, length=100, randomness=2), style():
        fig, ax = plt.subplots(figsize=(12, 6.3), dpi=100)
        bars = ax.bar(range(3), values, color=colors, edgecolor=INK, linewidth=2,
                      width=0.62)
        clean_axes(ax)
        ax.set_xticks(range(3), labels)
        ax.set_ylabel("maximum concurrency")
        ax.set_ylim(0, 13)
        ax.set_title("capacity planning Qwen3.8 on four B70s", loc="left", fontsize=24)
        ax.text(0.01, 0.91, "p95 time to first token below 10 seconds | MTP | native 256K",
                transform=ax.transAxes, color=MUTED, fontsize=12)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.45, f"C={value}",
                    ha="center", fontsize=17, fontweight="bold")
        finish(fig, "card.svg", title, description, pad=0.1)


if __name__ == "__main__":
    boundary_trials()
    throughput_vs_slo()
    capacity_envelope()
    protocol()
    social_card()
