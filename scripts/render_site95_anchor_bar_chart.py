#!/usr/bin/env python3
"""Render a simple bar chart showing why site 95 was chosen as anchor."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt


DATA_DIR = Path("./data/TrafficGeneration/dublin_march_2025")
SITE_METADATA = DATA_DIR / "site_metadata.csv"
DETECTOR_DATA = DATA_DIR / "detector_data.csv"
OUTPUT = DATA_DIR / "site_95_anchor_bar_chart.png"


def load_metadata():
    with SITE_METADATA.open() as handle:
        return {row["site_id"]: row for row in csv.DictReader(handle)}


def load_filtered_candidates():
    metadata = load_metadata()
    candidates = []
    with DETECTOR_DATA.open() as handle:
        for row in csv.DictReader(handle):
            site_id = row["site_id"]
            meta = metadata.get(site_id)
            if not meta:
                continue
            if meta["region_metadata"] != "CCITY":
                continue
            if meta["retained_for_topology"] != "True" or meta["missing_coordinates"] != "False":
                continue
            peak_hour = max(float(row[f"h{hour:02d}"]) for hour in range(24))
            if not (250.0 <= peak_hour <= 700.0):
                continue
            candidates.append(
                {
                    "site_id": site_id,
                    "peak_hour": peak_hour,
                    "description": meta["site_description"],
                    "distance_to_500": abs(peak_hour - 500.0),
                }
            )
    candidates.sort(key=lambda item: (item["peak_hour"], int(item["site_id"])))
    return candidates


def render():
    candidates = load_filtered_candidates()
    site95 = next(candidate for candidate in candidates if candidate["site_id"] == "95")

    labels = [candidate["site_id"] for candidate in candidates]
    values = [candidate["peak_hour"] for candidate in candidates]
    colors = ["#93c5fd" if candidate["site_id"] != "95" else "#f97316" for candidate in candidates]

    fig, ax = plt.subplots(figsize=(14, 6.5))
    fig.suptitle("Selecting Site 95 as the Dublin Anchor Site", fontsize=20, fontweight="bold", y=0.98)

    ax.axhspan(250, 700, color="#dbeafe", alpha=0.55, label="candidate filter: 250-700 veh/h")
    ax.axhline(500, color="#2563eb", linestyle="--", linewidth=2, label="preferred moderate level: 500 veh/h")
    ax.bar(labels, values, color=colors, edgecolor="#1f2937", linewidth=0.8)

    idx95 = labels.index("95")
    ax.annotate(
        "Site 95\n632 veh/h\nfirst runnable SUMO site",
        xy=(idx95, site95["peak_hour"]),
        xytext=(idx95 - 9.2, site95["peak_hour"] + 42),
        arrowprops=dict(arrowstyle="->", lw=1.8, color="black"),
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.96),
    )

    ax.text(
        0.01,
        0.96,
        "All bars are topology-ready sites\nthat passed the peak-hour filter.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10.5,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#d1d5db", alpha=0.95),
    )

    ax.set_xlabel("SCATS site ID")
    ax.set_ylabel("Peak-hour traffic intensity (vehicles/hour)")
    ax.set_ylim(0, 760)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper right", frameon=True)
    plt.setp(ax.get_xticklabels(), rotation=70, ha="right", fontsize=9)

    fig.tight_layout()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    render()
