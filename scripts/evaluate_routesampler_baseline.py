#!/usr/bin/env python3
"""Evaluate a Dublin SUMO routeSampler baseline on one or more site folders."""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.machine_learning.training.sumo_site_metrics import collect_site_detector_profiles, compute_profile_metrics


SUMO_ROUTE_SAMPLER = Path("/usr/share/sumo/tools/routeSampler.py")
VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a routeSampler.py baseline against Dublin site profiles using the existing SUMO site folders."
    )
    parser.add_argument(
        "--site-ids",
        default="95,94,418,419,612,925,60,202",
        help="Comma-separated Dublin site ids to evaluate.",
    )
    parser.add_argument(
        "--training-root",
        default="./src/machine_learning/training",
        help="Root directory containing per-site SUMO folders.",
    )
    parser.add_argument(
        "--traffic-data-dir",
        default="./data/TrafficGeneration/dublin_march_2025",
        help="Directory containing detector_data.csv.",
    )
    parser.add_argument(
        "--candidate-multiplier",
        type=float,
        default=2.0,
        help="Multiplier for building an oversized candidate route set before route sampling.",
    )
    parser.add_argument(
        "--candidate-padding",
        type=int,
        default=100,
        help="Extra candidate vehicles to add beyond the multiplier-based count.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for routeSampler.py.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the baseline result JSON.",
    )
    return parser.parse_args()


def resolve_net_path(site_dir: Path) -> str:
    tree = ET.parse(site_dir / "sim.sumocfg")
    root = tree.getroot()
    node = root.find("./input/net-file")
    if node is None or not node.get("value"):
        raise RuntimeError(f"{site_dir}/sim.sumocfg is missing <input>/<net-file value=...>.")
    return node.get("value")


def resolve_detector_edge(site_dir: Path) -> str:
    tree = ET.parse(site_dir / "detectors.add.xml")
    root = tree.getroot()
    loop = root.find("inductionLoop")
    if loop is None or not loop.get("lane"):
        raise RuntimeError(f"{site_dir}/detectors.add.xml is missing an inductionLoop lane.")
    lane = loop.get("lane")
    if lane.endswith("_0"):
        return lane[:-2]
    if "_" in lane:
        return lane.rsplit("_", 1)[0]
    return lane


def load_target_profiles(traffic_data_dir: Path, site_ids: list[str]) -> dict[str, list[int]]:
    profiles: dict[str, list[int]] = {}
    with (traffic_data_dir / "detector_data.csv").open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            site_id = str(row["site_id"]).strip()
            if site_id in site_ids:
                profiles[site_id] = [int(round(float(row[f"h{hour:02d}"]))) for hour in range(24)]
    missing = [site_id for site_id in site_ids if site_id not in profiles]
    if missing:
        raise RuntimeError(f"Missing site profiles for {missing}")
    return profiles


def load_route_edges(site_dir: Path) -> str:
    root = ET.parse(site_dir / "routes.rou.xml").getroot()
    vehicle = root.find("vehicle")
    if vehicle is None:
        raise RuntimeError(f"{site_dir}/routes.rou.xml has no vehicle entries.")
    route = vehicle.find("route")
    if route is None or not route.get("edges"):
        raise RuntimeError(f"{site_dir}/routes.rou.xml has no route edges.")
    return route.get("edges")


def write_candidate_routes(site_dir: Path, route_edges: str, candidate_count: int) -> Path:
    route_file = site_dir / "routesampler_candidates.rou.xml"
    with route_file.open("w", encoding="utf-8") as handle:
        handle.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        handle.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ')
        handle.write('xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n')
        for index in range(candidate_count):
            depart = (86400.0 * index) / max(candidate_count, 1)
            handle.write(
                f'    <vehicle id="cand_{index}" depart="{depart:.2f}" departLane="random" departSpeed="max">'
                f'<route edges="{route_edges}"/></vehicle>\n'
            )
        handle.write("</routes>\n")
    return route_file


def write_edge_counts(site_dir: Path, detector_edge: str, target_profile: list[int]) -> Path:
    counts_file = site_dir / "routesampler_counts.xml"
    with counts_file.open("w", encoding="utf-8") as handle:
        handle.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        handle.write("<meandata>\n")
        for hour, count in enumerate(target_profile):
            begin = hour * 3600
            end = begin + 3600
            handle.write(f'    <interval begin="{begin}" end="{end}">\n')
            handle.write(f'        <edge id="{detector_edge}" entered="{count}"/>\n')
            handle.write("    </interval>\n")
        handle.write("</meandata>\n")
    return counts_file


def write_temp_sumocfg(site_dir: Path, net_file: str, route_file_name: str) -> Path:
    cfg_path = site_dir / "routesampler_eval.sumocfg"
    cfg_path.write_text(
        "<configuration>\n"
        "    <input>\n"
        f'        <net-file value="{net_file}"/>\n'
        '        <additional-files value="detectors.add.xml"/>\n'
        f'        <route-files value="{route_file_name}"/>\n'
        "    </input>\n\n"
        "    <time>\n"
        '        <begin value="0"/>\n'
        "    </time>\n\n"
        "    <processing>\n"
        '        <time-to-teleport value="300"/>\n'
        "    </processing>\n"
        "</configuration>\n",
        encoding="utf-8",
    )
    return cfg_path


def run_routesampler(site_dir: Path, candidate_routes: Path, counts_file: Path, seed: int) -> Path:
    output_routes = site_dir / "routesampler_output.rou.xml"
    subprocess.run(
        [
            str(VENV_PYTHON),
            str(SUMO_ROUTE_SAMPLER),
            "-r",
            candidate_routes.name,
            "-d",
            counts_file.name,
            "--edgedata-attribute",
            "entered",
            "--write-flows",
            "number",
            "-o",
            output_routes.name,
            "-s",
            str(seed),
            "-b",
            "0",
            "-e",
            "86400",
            "-i",
            "3600",
        ],
        cwd=site_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return output_routes


def run_sumo(site_dir: Path, sumocfg: Path) -> None:
    subprocess.run(
        ["sumo", "-c", sumocfg.name, "--no-warnings"],
        cwd=site_dir,
        check=True,
        capture_output=True,
        text=True,
    )


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values)) / float(len(values))


def main() -> None:
    args = parse_args()
    site_ids = [site_id.strip() for site_id in args.site_ids.split(",") if site_id.strip()]
    training_root = Path(args.training_root).resolve()
    traffic_data_dir = Path(args.traffic_data_dir).resolve()
    output_path = Path(args.output).resolve()

    target_profiles = load_target_profiles(traffic_data_dir, site_ids)
    per_site = {}

    for site_id in site_ids:
        site_dir = training_root / site_id
        route_edges = load_route_edges(site_dir)
        detector_edge = resolve_detector_edge(site_dir)
        target_profile = target_profiles[site_id]
        total_target = sum(target_profile)
        candidate_count = max(
            int(math.ceil(total_target * args.candidate_multiplier)) + args.candidate_padding,
            max(target_profile) * 24,
        )

        candidate_routes = write_candidate_routes(site_dir, route_edges, candidate_count)
        counts_file = write_edge_counts(site_dir, detector_edge, target_profile)
        sampled_routes = run_routesampler(site_dir, candidate_routes, counts_file, args.seed)
        temp_sumocfg = write_temp_sumocfg(site_dir, resolve_net_path(site_dir), sampled_routes.name)
        run_sumo(site_dir, temp_sumocfg)

        _, simulated_profile = collect_site_detector_profiles(site_dir)
        metrics = compute_profile_metrics(target_profile, simulated_profile)
        per_site[site_id] = {
            "target_profile": target_profile,
            "simulated_profile": simulated_profile,
            "hourly_error": metrics["hourly_error"],
            "hourly_absolute_error": metrics["hourly_absolute_error"],
            "profile_mae": metrics["mae"],
            "profile_rmse": metrics["rmse"],
            "total_target": metrics["total_target"],
            "total_simulated": metrics["total_simulated"],
            "daily_mean_target": metrics["daily_mean_target"],
            "daily_mean_simulated": metrics["daily_mean_simulated"],
            "detector_edge": detector_edge,
            "candidate_route_count": candidate_count,
        }

    report = {
        "baseline": "SUMO routeSampler.py",
        "site_ids": site_ids,
        "seed": args.seed,
        "candidate_multiplier": args.candidate_multiplier,
        "candidate_padding": args.candidate_padding,
        "per_site": per_site,
        "summary": {
            "mean_profile_mae": mean([site_report["profile_mae"] for site_report in per_site.values()]),
            "mean_profile_rmse": mean([site_report["profile_rmse"] for site_report in per_site.values()]),
            "mean_daily_mean_target": mean([site_report["daily_mean_target"] for site_report in per_site.values()]),
            "mean_daily_mean_simulated": mean([site_report["daily_mean_simulated"] for site_report in per_site.values()]),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
