#!/usr/bin/env python3
"""Render the reduced 8-site decentralized round-scaling figure."""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = REPO_ROOT / "docs" / "figures"
OUT_DIR = REPO_ROOT / "output" / "figures"
LOG_PATH = REPO_ROOT / "8siteExperiments.md"

ROUND_RUNS = {
    1: REPO_ROOT / "output" / "decentralized_sim" / "dublin_fast_8_hourly_sumo_r1_smoke.json",
    2: REPO_ROOT / "output" / "decentralized_sim" / "dublin_fast_8_hourly_sumo_r2_smoke.json",
    4: REPO_ROOT / "output" / "decentralized_sim" / "dublin_fast_8_hourly_sumo_r4_smoke.json",
    5: REPO_ROOT / "output" / "decentralized_sim" / "dublin_fast_8_hourly_sumo_r5_smoke.json",
}

FIG_PNG = FIG_DIR / "dublin_8site_round_scaling_tradeoff.png"
FIG_PDF = FIG_DIR / "dublin_8site_round_scaling_tradeoff.pdf"
SUMMARY_JSON = OUT_DIR / "dublin_8site_round_scaling_summary.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def mean_profile_mae_by_round(run: dict) -> list[float]:
    site_ids = list(run["profile_mae"].keys())
    round_count = len(run["profile_mae"][site_ids[0]])
    values = []
    for round_index in range(round_count):
        round_mean = float(np.mean([run["profile_mae"][site_id][round_index] for site_id in site_ids]))
        values.append(round_mean)
    return values


def parse_duration_minutes(text: str) -> dict[int, float]:
    pattern = re.compile(
        r"## .*?Smoke, `r=(\d+)`, `1/1/1`.*?- Wall-clock duration:\n  - about `(\d+)m(\d+)s`",
        re.DOTALL,
    )
    durations = {}
    for round_text, minutes_text, seconds_text in pattern.findall(text):
        round_id = int(round_text)
        durations[round_id] = int(minutes_text) + int(seconds_text) / 60.0
    return durations


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    durations_text = LOG_PATH.read_text(encoding="utf-8")
    duration_minutes = parse_duration_minutes(durations_text)

    rounds = sorted(ROUND_RUNS.keys())
    round_means = {}
    final_round_mae = []
    runtimes = []

    for round_id in rounds:
        run = load_json(ROUND_RUNS[round_id])
        means = mean_profile_mae_by_round(run)
        round_means[round_id] = means
        final_round_mae.append(means[-1])
        runtimes.append(duration_minutes[round_id])

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.3))

    ax_left = axes[0]
    ax_left.plot(
        rounds,
        final_round_mae,
        color="#1f4fff",
        marker="o",
        linewidth=2.2,
        markersize=7.0,
        label="Final-round mean profile MAE",
    )
    ax_left.set_xlabel("Federated rounds")
    ax_left.set_ylabel("Final-round mean profile MAE", color="#1f4fff")
    ax_left.tick_params(axis="y", labelcolor="#1f4fff")
    ax_left.set_xticks(rounds)
    ax_left.grid(True, linestyle="--", linewidth=0.8, alpha=0.4)

    ax_left_right = ax_left.twinx()
    ax_left_right.plot(
        rounds,
        runtimes,
        color="#d94841",
        marker="s",
        linewidth=2.0,
        markersize=6.2,
        linestyle="--",
        label="Wall-clock runtime",
    )
    ax_left_right.set_ylabel("Wall-clock runtime (minutes)", color="#d94841")
    ax_left_right.tick_params(axis="y", labelcolor="#d94841")

    left_lines, left_labels = ax_left.get_legend_handles_labels()
    right_lines, right_labels = ax_left_right.get_legend_handles_labels()
    ax_left.legend(left_lines + right_lines, left_labels + right_labels, loc="upper left", frameon=True)
    ax_left.set_title("Final-round accuracy versus runtime")

    ax_right = axes[1]
    palette = {
        1: "#2a9d8f",
        2: "#f4a261",
        4: "#6c5ce7",
        5: "#e76f51",
    }
    for round_id in rounds:
        x = np.arange(1, len(round_means[round_id]) + 1)
        ax_right.plot(
            x,
            round_means[round_id],
            marker="o",
            linewidth=2.0,
            markersize=5.8,
            color=palette[round_id],
            label=fr"Run with $r={round_id}$",
        )
    ax_right.set_xlabel("Observed round within run")
    ax_right.set_ylabel("Mean profile MAE")
    ax_right.set_title("Within-run metric drift")
    ax_right.grid(True, linestyle="--", linewidth=0.8, alpha=0.4)
    ax_right.legend(loc="upper left", frameon=True)

    fig.suptitle("Dublin 8-site decentralized round scaling", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(FIG_PNG, dpi=220, bbox_inches="tight")
    fig.savefig(FIG_PDF, bbox_inches="tight")
    plt.close(fig)

    summary = {
        "source_runs": {str(round_id): str(path) for round_id, path in ROUND_RUNS.items()},
        "duration_minutes": duration_minutes,
        "final_round_mean_profile_mae": {
            str(round_id): float(final_round_mae[idx]) for idx, round_id in enumerate(rounds)
        },
        "within_run_mean_profile_mae": {
            str(round_id): [float(value) for value in round_means[round_id]] for round_id in rounds
        },
        "png_output": str(FIG_PNG),
        "pdf_output": str(FIG_PDF),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
