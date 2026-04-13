#!/usr/bin/env python3
"""Render Dublin dendrograms for volume and pattern affinity groupings."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOPOLOGY = REPO_ROOT / "config" / "dublin_voronoi_fast_8.json"
DEFAULT_DATASET = REPO_ROOT / "data" / "TrafficGeneration" / "dublin_march_2025" / "detector_data.csv"
DEFAULT_PNG = REPO_ROOT / "docs" / "figures" / "dublin_affinity_dendrograms.png"
DEFAULT_PDF = REPO_ROOT / "docs" / "figures" / "dublin_affinity_dendrograms.pdf"
DEFAULT_JSON = REPO_ROOT / "output" / "figures" / "dublin_affinity_dendrograms_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Dublin dendrograms for the reduced 8-site subset.")
    parser.add_argument("--topology", default=str(DEFAULT_TOPOLOGY), help="Topology JSON whose site ordering is used.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET), help="Path to detector_data.csv.")
    parser.add_argument("--clusters", type=int, default=3, help="Number of clusters to highlight.")
    parser.add_argument("--png-output", default=str(DEFAULT_PNG), help="PNG output path.")
    parser.add_argument("--pdf-output", default=str(DEFAULT_PDF), help="PDF output path.")
    parser.add_argument("--json-output", default=str(DEFAULT_JSON), help="Summary JSON output path.")
    return parser.parse_args()


def load_site_ids(topology_path: Path) -> list[str]:
    with topology_path.open("r", encoding="utf-8") as handle:
        topology = json.load(handle)
    return list(topology.keys())


def load_profiles(dataset_path: Path, site_ids: list[str]) -> dict[str, np.ndarray]:
    profiles: dict[str, np.ndarray] = {}
    with dataset_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            site_id = str(row["site_id"]).strip()
            if site_id in site_ids:
                profiles[site_id] = np.array([float(row[f"h{hour:02d}"]) for hour in range(24)], dtype=float)
    missing = [site_id for site_id in site_ids if site_id not in profiles]
    if missing:
        raise RuntimeError(f"Missing site profiles for: {missing}")
    return profiles


def zscore_rows(matrix: np.ndarray) -> np.ndarray:
    mean = matrix.mean(axis=1, keepdims=True)
    std = matrix.std(axis=1, keepdims=True)
    std[std == 0.0] = 1.0
    return (matrix - mean) / std


def cluster_threshold(z: np.ndarray, clusters: int) -> float:
    if clusters <= 1:
        return float("inf")
    n = z.shape[0] + 1
    merge_index = n - clusters - 1
    if merge_index < 0:
        return z[0, 2] / 2.0
    return float(z[merge_index, 2] + 1e-9)


def cluster_groups(site_ids: list[str], z: np.ndarray, clusters: int) -> list[list[str]]:
    labels = fcluster(z, t=clusters, criterion="maxclust")
    grouped: dict[int, list[str]] = {}
    for site_id, label in zip(site_ids, labels):
        grouped.setdefault(int(label), []).append(site_id)
    return sorted(grouped.values(), key=lambda members: (len(members), members))


def group_text(groups: list[list[str]]) -> str:
    return " | ".join("{" + ", ".join(group) + "}" for group in groups)


def render_panel(ax: plt.Axes, matrix: np.ndarray, site_ids: list[str], title: str, clusters: int) -> tuple[np.ndarray, list[list[str]]]:
    z = linkage(matrix, method="ward", optimal_ordering=True)
    threshold = cluster_threshold(z, clusters)
    dendrogram(
        z,
        labels=site_ids,
        leaf_rotation=0,
        leaf_font_size=11,
        color_threshold=threshold,
        above_threshold_color="#8c8c8c",
        ax=ax,
    )
    ax.axhline(threshold, color="#b22222", linestyle="--", linewidth=1.2, alpha=0.8)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_ylabel("Ward linkage distance")
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.6, alpha=0.7)
    groups = cluster_groups(site_ids, z, clusters)
    ax.text(
        0.5,
        -0.20,
        f"{clusters} clusters: {group_text(groups)}",
        ha="center",
        va="top",
        transform=ax.transAxes,
        fontsize=10.5,
    )
    return z, groups


def main() -> None:
    args = parse_args()
    topology_path = Path(args.topology)
    dataset_path = Path(args.dataset)
    png_output = Path(args.png_output)
    pdf_output = Path(args.pdf_output)
    json_output = Path(args.json_output)

    site_ids = load_site_ids(topology_path)
    profiles = load_profiles(dataset_path, site_ids)
    raw_matrix = np.stack([profiles[site_id] for site_id in site_ids])
    pattern_matrix = zscore_rows(raw_matrix)

    fig, axes = plt.subplots(1, 2, figsize=(15, 7.4))
    fig.suptitle("Dublin Reduced 8-Site Dendrograms", fontsize=16, fontweight="bold")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.90, bottom=0.22, wspace=0.10)

    _, volume_groups = render_panel(
        axes[0],
        raw_matrix,
        site_ids,
        "Traffic Volume Affinity",
        args.clusters,
    )
    _, pattern_groups = render_panel(
        axes[1],
        pattern_matrix,
        site_ids,
        "Traffic Pattern Affinity",
        args.clusters,
    )

    fig.text(
        0.5,
        0.03,
        "Volume uses raw 24-hour site totals. Pattern uses per-site z-scored daily profiles.",
        ha="center",
        fontsize=10,
    )

    png_output.parent.mkdir(parents=True, exist_ok=True)
    pdf_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(png_output, dpi=220, bbox_inches="tight")
    fig.savefig(pdf_output, bbox_inches="tight")
    plt.close(fig)

    summary = {
        "site_ids": site_ids,
        "clusters": args.clusters,
        "volume_groups": volume_groups,
        "pattern_groups": pattern_groups,
        "png_output": str(png_output),
        "pdf_output": str(pdf_output),
    }
    json_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
