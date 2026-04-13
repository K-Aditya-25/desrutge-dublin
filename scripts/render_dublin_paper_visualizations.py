#!/usr/bin/env python3
"""Render Dublin adaptations of the paper's main visualization figures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patheffects as pe


REPO_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = REPO_ROOT / "docs" / "figures"
SUMMARY_PATH = REPO_ROOT / "output" / "figures" / "dublin_paper_visualizations_summary.json"

DES_RUN_PATH = REPO_ROOT / "output" / "decentralized_sim" / "dublin_fast_8_hourly_sumo_r1_smoke.json"
GEO_RUN_PATH = REPO_ROOT / "output" / "decentralized_sim" / "dublin_fast_8_hourly_sumo_r5_smoke.json"
PATTERN_RUN_PATH = REPO_ROOT / "output" / "decentralized_sim" / "dublin_fast_8_pattern_affinity_r5_smoke.json"
VOLUME_RUN_PATH = REPO_ROOT / "output" / "decentralized_sim" / "dublin_fast_8_volume_affinity_r5_smoke.json"
ROUTESAMPLER_PATH = REPO_ROOT / "output" / "routesampler" / "dublin_fast_8_routesampler_baseline.json"

FIG1_PNG = FIG_DIR / "dublin_paper_fig1_single_site_validation.png"
FIG1_PDF = FIG_DIR / "dublin_paper_fig1_single_site_validation.pdf"
FIG2_PNG = FIG_DIR / "dublin_paper_fig2_are_proxy_rounds.png"
FIG2_PDF = FIG_DIR / "dublin_paper_fig2_are_proxy_rounds.pdf"
FIG3_PNG = FIG_DIR / "dublin_paper_fig3_profile_comparison.png"
FIG3_PDF = FIG_DIR / "dublin_paper_fig3_profile_comparison.pdf"
FIG4_PNG = FIG_DIR / "dublin_all_sites_profile_comparison.png"
FIG4_PDF = FIG_DIR / "dublin_all_sites_profile_comparison.pdf"

TARGET_COLOR = "#f4b400"
TARGET_PATH_EFFECTS = [pe.Stroke(linewidth=3.2, foreground="white"), pe.Normal()]


def plot_target_series(ax: plt.Axes, hours: np.ndarray, target: np.ndarray, label: str = "Target") -> None:
    line = ax.plot(
        hours,
        target,
        color=TARGET_COLOR,
        marker="o",
        linestyle="--",
        linewidth=1.9,
        markersize=4.8,
        markeredgecolor="#222222",
        markeredgewidth=0.45,
        label=label,
        zorder=6,
    )[0]
    line.set_path_effects(TARGET_PATH_EFFECTS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Dublin versions of the paper-style plots.")
    parser.add_argument("--summary-output", default=str(SUMMARY_PATH), help="Path to write the summary JSON.")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def clean_series(values: list[float]) -> np.ndarray:
    return np.asarray(values, dtype=float)


def daily_mean_by_site(des_run: dict) -> list[tuple[str, float]]:
    rows = []
    for site_id, means in des_run["daily_mean_target"].items():
        rows.append((site_id, float(means[0])))
    return sorted(rows, key=lambda item: item[1])


def plot_fig1(des_run: dict, site_id: str) -> dict:
    hours = np.arange(24)
    target = clean_series(des_run["target_profile"][site_id][0])
    simulated = clean_series(des_run["simulated_profile"][site_id][0])

    fig, ax = plt.subplots(figsize=(8.6, 5.8))
    plot_target_series(ax, hours, target, label="Target")
    ax.plot(
        hours,
        simulated,
        color="#1f4fff",
        marker="s",
        linestyle="-",
        linewidth=1.8,
        markersize=6.8,
        label=f"DesRUTGe on site {site_id}",
        zorder=4,
    )
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Traffic intensity (vehicles/hour)")
    ax.set_title(f"Dublin Single-Site Validation on Site {site_id}", fontsize=14, fontweight="bold")
    ax.set_xticks(hours)
    ax.grid(True, linestyle="--", linewidth=1.0, alpha=0.45)
    ax.legend(loc="lower right", frameon=True)
    fig.tight_layout()
    fig.savefig(FIG1_PNG, dpi=220, bbox_inches="tight")
    fig.savefig(FIG1_PDF, bbox_inches="tight")
    plt.close(fig)

    return {
        "site_id": site_id,
        "profile_mae": float(des_run["profile_mae"][site_id][0]),
        "profile_rmse": float(des_run["profile_rmse"][site_id][0]),
        "daily_mean_target": float(des_run["daily_mean_target"][site_id][0]),
        "daily_mean_simulated": float(des_run["daily_mean_simulated"][site_id][0]),
        "png_output": str(FIG1_PNG),
        "pdf_output": str(FIG1_PDF),
    }


def strategy_profile_mae_by_site(strategy_run: dict) -> dict[str, list[float]]:
    return {
        site_id: [float(value) for value in per_round_values]
        for site_id, per_round_values in strategy_run["profile_mae"].items()
    }


def plot_fig2(volume_run: dict, pattern_run: dict, geographic_run: dict) -> dict:
    rounds = np.arange(1, len(next(iter(volume_run["target_profile"].values()))) + 1)
    strategy_values = {
        "Volume Similarity": strategy_profile_mae_by_site(volume_run),
        "Pattern Similarity": strategy_profile_mae_by_site(pattern_run),
        "Geographic Neighbors": strategy_profile_mae_by_site(geographic_run),
    }
    ordered_sites = list(volume_run["target_profile"].keys())

    fig, axes = plt.subplots(1, 3, figsize=(21.0, 6.4), sharey=True)
    for ax, (title, values_by_site) in zip(axes, strategy_values.items()):
        for site_id in ordered_sites:
            ax.plot(
                rounds,
                values_by_site[site_id],
                marker="o",
                linestyle="--",
                linewidth=1.0,
                markersize=4.8,
                label=site_id,
            )
        ax.set_title(title, fontsize=14)
        ax.set_xlabel("Round", fontsize=12)
        ax.set_xticks(rounds)
        ax.tick_params(axis="both", labelsize=10)
        ax.grid(True, linestyle="--", linewidth=0.7, alpha=0.45)
    axes[0].set_ylabel("Profile MAE", fontsize=12)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper right",
        bbox_to_anchor=(0.988, 0.988),
        ncol=2,
        fontsize=11,
        frameon=True,
        borderaxespad=0.4,
    )
    fig.suptitle("Dublin Model-Exchange Comparison Across Rounds", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 0.86, 0.96])
    fig.savefig(FIG2_PNG, dpi=220, bbox_inches="tight")
    fig.savefig(FIG2_PDF, bbox_inches="tight")
    plt.close(fig)

    strategy_means = {
        title: {
            "round_means": [
                float(np.mean([values_by_site[site_id][idx] for site_id in ordered_sites]))
                for idx in range(len(rounds))
            ]
        }
        for title, values_by_site in strategy_values.items()
    }

    return {
        "metric_note": (
            "This figure now uses the saved per-round profile_mae values directly, averaged over the 24-hour "
            "daily profile for each site and round."
        ),
        "per_strategy_per_site": strategy_values,
        "per_strategy_round_means": strategy_means,
        "png_output": str(FIG2_PNG),
        "pdf_output": str(FIG2_PDF),
    }


def plot_fig3(des_run: dict, routesampler_run: dict, representative_sites: list[tuple[str, str]]) -> dict:
    hours = np.arange(24)
    fig, axes = plt.subplots(1, 3, figsize=(18.0, 5.1))

    site_summary: dict[str, dict] = {}
    for ax, (site_id, label) in zip(axes, representative_sites):
        target = clean_series(des_run["target_profile"][site_id][0])
        des = clean_series(des_run["simulated_profile"][site_id][0])
        rs = clean_series(routesampler_run["per_site"][site_id]["simulated_profile"])

        plot_target_series(ax, hours, target, label="Target")
        ax.plot(hours, des, color="#1f4fff", marker="s", linestyle="-", linewidth=1.7, markersize=4.5, label="DesRUTGe", zorder=4)
        ax.plot(hours, rs, color="#e53935", marker="^", linestyle="-", linewidth=1.3, markersize=4.2, label="routeSampler.py", zorder=3)
        ax.set_title(f"Site {site_id} ({label})", fontsize=12.5)
        ax.set_xlabel("Hour of day")
        ax.set_ylabel("Traffic intensity (vehicles/hour)")
        ax.set_xticks(hours)
        ax.tick_params(axis="x", labelsize=8)
        ax.grid(True, linestyle="--", linewidth=0.7, alpha=0.45)

        site_summary[site_id] = {
            "label": label,
            "daily_mean_target": float(des_run["daily_mean_target"][site_id][0]),
            "des_profile_mae": float(des_run["profile_mae"][site_id][0]),
            "routesampler_profile_mae": float(routesampler_run["per_site"][site_id]["profile_mae"]),
        }

    axes[1].legend(loc="lower center", bbox_to_anchor=(0.5, -0.24), ncol=3, frameon=True)
    fig.suptitle("Representative Dublin Traffic Profiles", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=[0, 0.05, 1, 0.96])
    fig.savefig(FIG3_PNG, dpi=220, bbox_inches="tight")
    fig.savefig(FIG3_PDF, bbox_inches="tight")
    plt.close(fig)

    return {
        "note": (
            "The paper's Figure 7 compares DesRUTGe against the earlier centralized RUTGe method. "
            "That exact multi-site comparison is not reconstructible from the saved Dublin runs because the "
            "current centralized exports preserve only the server site. This Dublin adaptation therefore uses "
            "the available multi-site baseline, SUMO's routeSampler.py, to keep the three representative-site "
            "comparison fully grounded in existing outputs."
        ),
        "representative_sites": site_summary,
        "png_output": str(FIG3_PNG),
        "pdf_output": str(FIG3_PDF),
    }


def plot_fig4_all_sites(des_run: dict, routesampler_run: dict, ordered_sites: list[tuple[str, float]]) -> dict:
    hours = np.arange(24)
    fig, axes = plt.subplots(4, 2, figsize=(8.27, 11.3), sharex=True)
    axes = axes.flatten()

    site_summary: dict[str, dict] = {}
    for ax, (site_id, daily_mean) in zip(axes, ordered_sites):
        target = clean_series(des_run["target_profile"][site_id][0])
        des = clean_series(des_run["simulated_profile"][site_id][0])
        rs = clean_series(routesampler_run["per_site"][site_id]["simulated_profile"])

        plot_target_series(ax, hours, target, label="Target")
        ax.plot(hours, des, color="#1f4fff", marker="s", linestyle="-", linewidth=1.3, markersize=2.7, label="DesRUTGe", zorder=4)
        ax.plot(hours, rs, color="#e53935", marker="^", linestyle="-", linewidth=1.1, markersize=2.5, label="routeSampler.py", zorder=3)
        ax.set_title(f"Site {site_id}", fontsize=10.5, fontweight="bold", pad=4)
        ax.set_xticks(np.arange(0, 24, 3))
        ax.tick_params(axis="both", labelsize=8)
        ax.grid(True, linestyle="--", linewidth=0.55, alpha=0.40)
        robust_ceiling = max(float(np.max(target)), float(np.max(des)), float(np.percentile(rs, 95)))
        raw_ceiling = max(float(np.max(target)), float(np.max(des)), float(np.max(rs)))
        if raw_ceiling > robust_ceiling * 1.6:
            ax.set_ylim(0, robust_ceiling * 1.10)
            ax.text(
                0.98,
                0.96,
                f"outlier clipped\nmax RS={raw_ceiling:.0f}",
                transform=ax.transAxes,
                va="top",
                ha="right",
                fontsize=7.0,
                color="#b71c1c",
                bbox={"boxstyle": "round,pad=0.22", "facecolor": "#fff5f5", "alpha": 0.86, "edgecolor": "#ef9a9a"},
            )
        ax.text(
            0.02,
            0.96,
            (
                f"mean={daily_mean:.1f}\n"
                f"MAE D={des_run['profile_mae'][site_id][0]:.1f}\n"
                f"MAE RS={routesampler_run['per_site'][site_id]['profile_mae']:.1f}"
            ),
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=7.2,
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "alpha": 0.82, "edgecolor": "#cccccc"},
        )

        site_summary[site_id] = {
            "daily_mean_target": float(daily_mean),
            "des_profile_mae": float(des_run["profile_mae"][site_id][0]),
            "routesampler_profile_mae": float(routesampler_run["per_site"][site_id]["profile_mae"]),
        }

    for row in range(4):
        axes[row * 2].set_ylabel("Vehicles/hour", fontsize=9)
    for ax in axes[-2:]:
        ax.set_xlabel("Hour of day", fontsize=9)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=True, fontsize=9, bbox_to_anchor=(0.5, 0.028))
    fig.suptitle("Dublin 8-Site Traffic Profile Comparison", fontsize=15, fontweight="bold", y=0.988)
    fig.text(
        0.5,
        0.012,
        "Sites are ordered by increasing target daily mean. Each subplot uses its own y-axis scale for readability.",
        ha="center",
        fontsize=8.5,
    )
    fig.subplots_adjust(left=0.09, right=0.985, top=0.94, bottom=0.08, hspace=0.34, wspace=0.16)
    fig.savefig(FIG4_PNG, dpi=220, bbox_inches="tight")
    fig.savefig(FIG4_PDF, bbox_inches="tight")
    plt.close(fig)

    return {
        "note": (
            "All eight Dublin reduced-subset sites are shown on a single A4-friendly portrait page. "
            "Sites are ordered by increasing target daily mean and use independent y-axis scales so that "
            "low-volume and high-volume sites remain visually interpretable on the same page."
        ),
        "ordered_sites": [site_id for site_id, _ in ordered_sites],
        "per_site": site_summary,
        "png_output": str(FIG4_PNG),
        "pdf_output": str(FIG4_PDF),
    }


def main() -> None:
    args = parse_args()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    Path(args.summary_output).parent.mkdir(parents=True, exist_ok=True)

    des_run = load_json(DES_RUN_PATH)
    geographic_run = load_json(GEO_RUN_PATH)
    pattern_run = load_json(PATTERN_RUN_PATH)
    volume_run = load_json(VOLUME_RUN_PATH)
    routesampler_run = load_json(ROUTESAMPLER_PATH)

    sorted_sites = daily_mean_by_site(des_run)
    summary = {
        "source_runs": {
            "des_single_round_best": str(DES_RUN_PATH),
            "geographic_round_sweep": str(GEO_RUN_PATH),
            "pattern_round_sweep": str(PATTERN_RUN_PATH),
            "volume_round_sweep": str(VOLUME_RUN_PATH),
            "routesampler_baseline": str(ROUTESAMPLER_PATH),
        },
        "selected_sites_by_intensity": sorted_sites,
    }

    # Site 94 is a clean medium-intensity example with near-perfect alignment.
    summary["figure_1"] = plot_fig1(des_run, site_id="94")
    summary["figure_2"] = plot_fig2(volume_run, pattern_run, geographic_run)

    # Representative sites selected to avoid the trivial near-zero and extreme-outlier cases.
    representative_sites = [("95", "low intensity"), ("202", "medium intensity"), ("419", "high intensity")]
    summary["figure_3"] = plot_fig3(des_run, routesampler_run, representative_sites)
    summary["figure_4_all_sites"] = plot_fig4_all_sites(des_run, routesampler_run, sorted_sites)

    Path(args.summary_output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
