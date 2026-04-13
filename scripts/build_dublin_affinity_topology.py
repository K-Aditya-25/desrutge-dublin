#!/usr/bin/env python3
"""Build an affinity-based Dublin topology from an existing subset topology."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Dublin affinity-based topology by regrouping an existing subset with Ward clustering."
    )
    parser.add_argument(
        "--input-topology",
        default="./config/dublin_voronoi_fast_8.json",
        help="Existing Dublin topology JSON whose nodes, ids, ports, and IPs are preserved.",
    )
    parser.add_argument(
        "--traffic-data-dir",
        default="./data/TrafficGeneration/dublin_march_2025",
        help="Directory containing detector_data.csv.",
    )
    parser.add_argument(
        "--mode",
        choices=["volume", "pattern"],
        required=True,
        help="Clustering mode: raw-volume similarity or standardized-pattern similarity.",
    )
    parser.add_argument(
        "--clusters",
        type=int,
        default=3,
        help="Number of Ward clusters to form.",
    )
    parser.add_argument(
        "--output-topology",
        required=True,
        help="Path to write the derived topology JSON.",
    )
    return parser.parse_args()


def load_profiles(traffic_data_dir: Path, site_ids: list[str]) -> dict[str, np.ndarray]:
    dataset_path = traffic_data_dir / "detector_data.csv"
    profiles: dict[str, np.ndarray] = {}
    with dataset_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            site_id = str(row["site_id"]).strip()
            if site_id in site_ids:
                profiles[site_id] = np.array([float(row[f"h{hour:02d}"]) for hour in range(24)], dtype=float)

    missing = [site_id for site_id in site_ids if site_id not in profiles]
    if missing:
        raise RuntimeError(f"Missing site profiles in detector_data.csv for: {missing}")
    return profiles


def normalize_for_pattern(profiles: np.ndarray) -> np.ndarray:
    mean = profiles.mean(axis=1, keepdims=True)
    std = profiles.std(axis=1, keepdims=True)
    std[std == 0] = 1.0
    return (profiles - mean) / std


def main() -> None:
    args = parse_args()
    input_topology = Path(args.input_topology)
    traffic_data_dir = Path(args.traffic_data_dir)
    output_topology = Path(args.output_topology)

    with input_topology.open("r", encoding="utf-8") as handle:
        topology = json.load(handle)

    site_ids = list(topology.keys())
    profiles = load_profiles(traffic_data_dir, site_ids)
    matrix = np.stack([profiles[site_id] for site_id in site_ids])

    if args.mode == "pattern":
        matrix = normalize_for_pattern(matrix)

    labels = AgglomerativeClustering(n_clusters=args.clusters, linkage="ward").fit_predict(matrix)

    clusters: dict[int, list[str]] = {}
    for site_id, label in zip(site_ids, labels):
        clusters.setdefault(int(label), []).append(site_id)

    affinity_topology = {}
    for site_id in site_ids:
        label = int(labels[site_ids.index(site_id)])
        neighbors = [int(other) for other in clusters[label] if other != site_id]
        affinity_topology[site_id] = {
            "id": topology[site_id]["id"],
            "ip": topology[site_id]["ip"],
            "port": topology[site_id]["port"],
            "neighbors": neighbors,
        }

    output_topology.parent.mkdir(parents=True, exist_ok=True)
    with output_topology.open("w", encoding="utf-8") as handle:
        json.dump(affinity_topology, handle, indent=2)

    print(json.dumps({"mode": args.mode, "clusters": clusters, "output_topology": str(output_topology)}, indent=2))


if __name__ == "__main__":
    main()
