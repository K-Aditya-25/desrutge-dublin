#!/usr/bin/env python3
"""Validate Dublin topology/config readiness for the DesRUTGe framework."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a Dublin topology JSON against the local traffic dataset and local SUMO site folders."
    )
    parser.add_argument("--topology", required=True, help="Path to a Dublin topology JSON.")
    parser.add_argument(
        "--traffic-data-dir",
        default="./data/TrafficGeneration/dublin_march_2025",
        help="Directory containing detector_data.csv.",
    )
    parser.add_argument(
        "--training-root",
        default="./src/machine_learning/training",
        help="Root directory containing per-site SUMO folders.",
    )
    parser.add_argument(
        "--traffic-simulation-mode",
        choices=["sumo", "test"],
        default="test",
        help="Framework mode to validate. 'sumo' requires local site folders for all topology nodes.",
    )
    return parser.parse_args()


def validate_topology_schema(topology: dict) -> list[str]:
    errors = []
    if not isinstance(topology, dict) or not topology:
        return ["Topology JSON must be a non-empty object keyed by site id."]

    for key, value in topology.items():
        if not isinstance(value, dict):
            errors.append(f"{key}: topology entry must be an object.")
            continue

        for required in ["id", "ip", "port", "neighbors"]:
            if required not in value:
                errors.append(f"{key}: missing required field '{required}'.")

        if "neighbors" in value and not isinstance(value["neighbors"], list):
            errors.append(f"{key}: neighbors must be a list.")

        if "port" in value and not isinstance(value["port"], int):
            errors.append(f"{key}: port must be an integer.")

    return errors


def main() -> None:
    args = parse_args()
    topology_path = Path(args.topology).resolve()
    traffic_dir = Path(args.traffic_data_dir).resolve()
    training_root = Path(args.training_root).resolve()

    topology = json.loads(topology_path.read_text(encoding="utf-8"))
    errors = validate_topology_schema(topology)

    detector_data = pd.read_csv(traffic_dir / "detector_data.csv", dtype={"site_id": str})
    known_sites = set(detector_data["site_id"].astype(str))
    topology_sites = sorted(topology.keys(), key=lambda value: (int(value) if value.isdigit() else value))

    missing_dataset_sites = [site_id for site_id in topology_sites if site_id not in known_sites]
    if missing_dataset_sites:
        errors.append(f"Topology sites missing from detector_data.csv: {missing_dataset_sites}")

    invalid_neighbors = []
    for site_id, node in topology.items():
        for neighbor in node.get("neighbors", []):
            neighbor_id = str(neighbor)
            if neighbor_id not in topology:
                invalid_neighbors.append((site_id, neighbor_id))
    if invalid_neighbors:
        errors.append(f"Topology references neighbors not present in the topology file: {invalid_neighbors}")

    missing_site_dirs = []
    if args.traffic_simulation_mode == "sumo":
        for site_id in topology_sites:
            if not (training_root / site_id).exists():
                missing_site_dirs.append(site_id)
        if missing_site_dirs:
            errors.append(
                "SUMO mode requires local site folders for every topology node. Missing site folders: "
                + str(missing_site_dirs)
            )

    if errors:
        raise SystemExit("Dublin framework validation failed:\n- " + "\n- ".join(errors))

    print(f"Topology file: {topology_path}")
    print(f"Traffic data dir: {traffic_dir}")
    print(f"Validated sites: {len(topology_sites)}")
    print(f"Traffic simulation mode: {args.traffic_simulation_mode}")
    print("Topology schema, dataset membership, and local site-folder checks passed.")
    if args.traffic_simulation_mode == "test":
        print("Note: 'test' mode validates Dublin framework readiness without requiring local SUMO folders for every site.")
    print("Note: local PPO execution may still fail on this MacBook due to OMP: Error #179: Can't open SHM2.")


if __name__ == "__main__":
    main()
