#!/usr/bin/env python3
"""Create a dissertation-ready figure explaining why site 95 was chosen as anchor."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


DATA_DIR = Path("./data/TrafficGeneration/dublin_march_2025")
SITE_METADATA = DATA_DIR / "site_metadata.csv"
DETECTOR_DATA = DATA_DIR / "detector_data.csv"
MAP_IMAGE = DATA_DIR / "voronoi_site_cells_fast_8_map_zones_labeled.png"
OUTPUT = DATA_DIR / "site_95_anchor_story.png"


def load_metadata():
    with SITE_METADATA.open() as handle:
        return {row["site_id"]: row for row in csv.DictReader(handle)}


def load_detector_rows():
    with DETECTOR_DATA.open() as handle:
        return list(csv.DictReader(handle))


def build_site_metrics(metadata, detector_rows):
    metrics = []
    for row in detector_rows:
        site_id = row["site_id"]
        meta = metadata.get(site_id)
        if not meta:
            continue
        hourly = np.array([float(row[f"h{hour:02d}"]) for hour in range(24)], dtype=float)
        metrics.append(
            {
                "site_id": site_id,
                "description": meta["site_description"],
                "region": meta["region_metadata"],
                "retained": meta["retained_for_topology"] == "True",
                "missing_coordinates": meta["missing_coordinates"] == "True",
                "hourly": hourly,
                "peak_hour": float(hourly.max()),
                "peak_hour_index": int(hourly.argmax()),
                "daily_total": float(hourly.sum()),
            }
        )
    return metrics


def make_figure():
    metadata = load_metadata()
    metrics = build_site_metrics(metadata, load_detector_rows())

    ccity = [
        row for row in metrics
        if row["region"] == "CCITY" and row["retained"] and not row["missing_coordinates"]
    ]
    filtered = [row for row in ccity if 250.0 <= row["peak_hour"] <= 700.0]
    site95 = next(row for row in metrics if row["site_id"] == "95")

    fig = plt.figure(figsize=(15, 11))
    grid = fig.add_gridspec(2, 2, height_ratios=[1, 1.05], width_ratios=[1.15, 1.0])

    ax_scatter = fig.add_subplot(grid[0, 0])
    ax_profile = fig.add_subplot(grid[0, 1])
    ax_map = fig.add_subplot(grid[1, 0])
    ax_pipeline = fig.add_subplot(grid[1, 1])

    fig.suptitle("Why Site 95 Became the Dublin Anchor Site", fontsize=21, fontweight="bold", y=0.97)

    # Panel A: city-centre filtering story.
    ax_scatter.axvspan(250, 700, color="#dbeafe", alpha=0.7, label="moderate peak filter: 250-700 veh/h")
    ax_scatter.axvline(500, color="#1d4ed8", linestyle="--", linewidth=2, label="preferred moderate target: 500 veh/h")
    ax_scatter.scatter(
        [row["peak_hour"] for row in ccity],
        [row["daily_total"] for row in ccity],
        s=22,
        color="#9ca3af",
        alpha=0.6,
        label="all topology-ready CCITY sites",
    )
    ax_scatter.scatter(
        [row["peak_hour"] for row in filtered],
        [row["daily_total"] for row in filtered],
        s=46,
        color="#60a5fa",
        alpha=0.9,
        label=f"filtered candidates (n={len(filtered)})",
    )
    ax_scatter.scatter(
        [site95["peak_hour"]],
        [site95["daily_total"]],
        s=180,
        marker="*",
        color="#f97316",
        edgecolor="black",
        linewidth=1.0,
        zorder=5,
        label="site 95",
    )
    ax_scatter.annotate(
        "Site 95\npeak = 632 veh/h\nchosen anchor",
        xy=(site95["peak_hour"], site95["daily_total"]),
        xytext=(site95["peak_hour"] + 55, site95["daily_total"] - 850),
        arrowprops=dict(arrowstyle="->", lw=1.8, color="black"),
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.96),
    )
    ax_scatter.set_title("1. Filter City-Centre Candidates by Traffic Intensity", fontsize=15, fontweight="bold", pad=10)
    ax_scatter.set_xlabel("Peak-hour traffic intensity (vehicles/hour)")
    ax_scatter.set_ylabel("Daily total traffic intensity (vehicles/day)")
    ax_scatter.grid(True, alpha=0.25)
    ax_scatter.legend(loc="upper left", fontsize=9, frameon=True)

    # Panel B: daily profile of site 95.
    hours = np.arange(24)
    ax_profile.plot(hours, site95["hourly"], color="#111827", linewidth=2.5)
    ax_profile.fill_between(hours, site95["hourly"], color="#f59e0b", alpha=0.25)
    ax_profile.scatter(
        [site95["peak_hour_index"]],
        [site95["peak_hour"]],
        s=90,
        color="#dc2626",
        zorder=4,
    )
    ax_profile.annotate(
        f"Peak at h{site95['peak_hour_index']:02d}\n{site95['peak_hour']:.0f} veh/h",
        xy=(site95["peak_hour_index"], site95["peak_hour"]),
        xytext=(site95["peak_hour_index"] - 6, site95["peak_hour"] - 145),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="black"),
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.96),
    )
    ax_profile.set_title("2. Site 95 Had a Moderate but Meaningful Daily Profile", fontsize=15, fontweight="bold", pad=10)
    ax_profile.set_xlabel("Hour of day")
    ax_profile.set_ylabel("Traffic intensity (vehicles/hour)")
    ax_profile.set_xticks(range(0, 24, 2))
    ax_profile.set_xlim(0, 23)
    ax_profile.grid(True, alpha=0.25)
    ax_profile.text(
        0.02,
        0.95,
        "JERVIS ST @ MARY ST\nRegion: CCITY",
        transform=ax_profile.transAxes,
        ha="left",
        va="top",
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#d1d5db", alpha=0.95),
    )

    # Panel C: map story.
    map_image = Image.open(MAP_IMAGE)
    crop = map_image.crop((30, 180, 450, 900))
    ax_map.imshow(crop)
    ax_map.set_title("3. Site 95 Sat Inside a Connected Inner-City Cluster", fontsize=15, fontweight="bold", pad=10)
    ax_map.axis("off")
    ax_map.text(
        0.03,
        0.04,
        "Site 95 sits near the centre of the compact city-core subset,\nmaking it a practical anchor from which neighbouring sites could be added.",
        transform=ax_map.transAxes,
        ha="left",
        va="bottom",
        fontsize=11,
        color="black",
        bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="black", alpha=0.94),
    )

    # Panel D: validation pipeline story.
    ax_pipeline.set_title("4. Site 95 Was the First Runnable Local SUMO Scenario", fontsize=15, fontweight="bold", pad=10)
    ax_pipeline.axis("off")
    steps = [
        ("Manual corridor\nin netedit", "#dbeafe"),
        ("Prepare site files:\nminiTAZ, detector,\nsumocfg, OD", "#e0f2fe"),
        ("od2trips", "#fde68a"),
        ("duarouter", "#fdba74"),
        ("sumo", "#fca5a5"),
        ("Validated anchor site", "#bbf7d0"),
    ]
    x_positions = [0.12, 0.36, 0.60, 0.76, 0.91, 0.60]
    y_positions = [0.72, 0.72, 0.72, 0.72, 0.72, 0.27]
    widths = [0.14, 0.22, 0.13, 0.13, 0.11, 0.22]
    box_height = 0.16
    for (label, color), x, y, width in zip(steps, x_positions, y_positions, widths):
        rect = plt.Rectangle((x - width / 2, y - box_height / 2), width, box_height, fc=color, ec="black", lw=1.5)
        ax_pipeline.add_patch(rect)
        ax_pipeline.text(x, y, label, ha="center", va="center", fontsize=10.5, fontweight="bold")

    arrow_style = dict(arrowstyle="->", lw=2, color="#111827")
    ax_pipeline.annotate("", xy=(0.25, 0.72), xytext=(0.19, 0.72), arrowprops=arrow_style)
    ax_pipeline.annotate("", xy=(0.51, 0.72), xytext=(0.47, 0.72), arrowprops=arrow_style)
    ax_pipeline.annotate("", xy=(0.69, 0.72), xytext=(0.66, 0.72), arrowprops=arrow_style)
    ax_pipeline.annotate("", xy=(0.86, 0.72), xytext=(0.82, 0.72), arrowprops=arrow_style)
    ax_pipeline.annotate("", xy=(0.60, 0.37), xytext=(0.91, 0.62), arrowprops=arrow_style)

    ax_pipeline.text(
        0.04,
        0.03,
        "Validation meant that a feasible source-detector-sink corridor had been identified\nand that the site could complete the full SUMO trip-generation and simulation pipeline without errors.",
        ha="left",
        va="bottom",
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#d1d5db", alpha=0.96),
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.subplots_adjust(top=0.90, hspace=0.25, wspace=0.22)
    fig.savefig(OUTPUT, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    make_figure()
