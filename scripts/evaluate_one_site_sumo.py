#!/usr/bin/env python3
"""Run one SUMO site directly against one Dublin traffic target row."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.machine_learning.training.sumo_site_metrics import collect_site_detector_profiles, compute_profile_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate one SUMO site against one hourly Dublin traffic target without loading the PPO stack."
    )
    parser.add_argument("--site-dir", required=True, help="Path to the SUMO site folder, e.g. ./src/machine_learning/training/95")
    parser.add_argument(
        "--traffic-data-dir",
        default="./data/TrafficGeneration/dublin_march_2025",
        help="Directory containing detector_data.csv",
    )
    parser.add_argument("--site-id", help="Site id to evaluate. Defaults to the site-dir folder name.")
    parser.add_argument(
        "--mode",
        choices=["hourly-debug", "daily-profile"],
        default="daily-profile",
        help="hourly-debug keeps the one-hour routing sanity check; daily-profile runs 24 independent hourly simulations.",
    )
    parser.add_argument(
        "--hour",
        type=int,
        default=0,
        help="Hour bucket to evaluate in hourly-debug mode, 0-23.",
    )
    parser.add_argument(
        "--demand",
        type=int,
        help="Override the injected OD demand in hourly-debug mode. If omitted, uses the chosen site's target count for --hour.",
    )
    return parser.parse_args()


def resolve_site_id(args: argparse.Namespace) -> str:
    if args.site_id:
        return str(args.site_id).strip()
    return Path(args.site_dir).resolve().name


def resolve_net_path(site_dir: Path) -> Path:
    tree = ET.parse(site_dir / "sim.sumocfg")
    root = tree.getroot()
    node = root.find("./input/net-file")
    if node is None or not node.get("value"):
        raise RuntimeError("sim.sumocfg is missing <input>/<net-file value=...>.")
    return site_dir / node.get("value")


def load_target_profile(traffic_data_dir: Path, site_id: str) -> list[int]:
    dataset_path = traffic_data_dir / "detector_data.csv"
    with dataset_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if str(row["site_id"]).strip() == site_id:
                return [int(float(row[f"h{hour:02d}"])) for hour in range(24)]
    raise RuntimeError(f"Site {site_id} not found in {dataset_path}.")


def write_od_file(site_dir: Path, demand: int) -> None:
    contents = f"""$OR;D2
0.00 1.00
1.0
taz taz {demand}"""
    (site_dir / "od_file.od").write_text(contents, encoding="utf-8")


def run_sumo_chain(site_dir: Path, net_path: Path) -> None:
    subprocess.run(
        ["od2trips", "-n", "miniTAZ.xml", "-d", "od_file.od", "-o", "trips.xml"],
        cwd=site_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "duarouter",
            "-n",
            net_path.name,
            "-t",
            "trips.xml",
            "-o",
            "routes.rou.xml",
            "--additional-files",
            "miniTAZ.xml",
            "--ignore-errors",
            "--no-warnings",
        ],
        cwd=site_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["sumo", "-c", "sim.sumocfg", "--no-warnings"],
        cwd=site_dir,
        check=True,
        capture_output=True,
        text=True,
    )


def run_hourly_debug(site_dir: Path, net_path: Path, target_profile: list[int], hour: int, demand_override: int | None) -> dict:
    demand = demand_override if demand_override is not None else target_profile[hour]
    write_od_file(site_dir, demand)
    run_sumo_chain(site_dir, net_path)
    per_detector, combined = collect_site_detector_profiles(site_dir)
    simulated_count = sum(combined)

    return {
        "mode": "hourly-debug",
        "evaluated_hour": hour,
        "target_hour_count": target_profile[hour],
        "injected_demand": demand,
        "simulated_hour_count": simulated_count,
        "hour_error": simulated_count - target_profile[hour],
        "simulated_profile": combined,
        "per_detector_profiles": per_detector,
    }


def run_daily_profile(site_dir: Path, net_path: Path, target_profile: list[int]) -> dict:
    simulated_profile = []
    per_hour_debug = []

    for hour, demand in enumerate(target_profile):
        write_od_file(site_dir, demand)
        run_sumo_chain(site_dir, net_path)
        per_detector, combined = collect_site_detector_profiles(site_dir)
        simulated_count = sum(combined)
        simulated_profile.append(simulated_count)
        per_hour_debug.append(
            {
                "hour": hour,
                "injected_demand": demand,
                "simulated_hour_count": simulated_count,
                "simulated_profile": combined,
                "per_detector_hour0": [profile[0] for profile in per_detector],
            }
        )

    metrics = compute_profile_metrics(target_profile, simulated_profile)
    return {
        "mode": "daily-profile",
        "target_profile": target_profile,
        "simulated_profile": simulated_profile,
        "hourly_error": metrics["hourly_error"],
        "hourly_absolute_error": metrics["hourly_absolute_error"],
        "mae": metrics["mae"],
        "rmse": metrics["rmse"],
        "total_target": metrics["total_target"],
        "total_simulated": metrics["total_simulated"],
        "daily_mean_target": metrics["daily_mean_target"],
        "daily_mean_simulated": metrics["daily_mean_simulated"],
        "per_hour_debug": per_hour_debug,
    }


def main() -> None:
    args = parse_args()
    if not 0 <= args.hour <= 23:
        raise ValueError("--hour must be between 0 and 23.")

    site_dir = Path(args.site_dir).resolve()
    traffic_data_dir = Path(args.traffic_data_dir).resolve()
    site_id = resolve_site_id(args)
    net_path = resolve_net_path(site_dir)
    target_profile = load_target_profile(traffic_data_dir, site_id)

    report = {
        "site_id": site_id,
        "site_dir": str(site_dir),
        "net_file": net_path.name,
        "traffic_metric_contract": {
            "target_profile": "One Dublin SCATS site row is the canonical 24-hour truth vector h00..h23.",
            "primary_local_metric": "Compare full 24-hour simulated detector profile against the full 24-hour target profile.",
            "ppo_scalar_adapter": "Collapse the simulated 24-hour detector profile to its daily mean.",
        },
    }

    if args.mode == "hourly-debug":
        report.update(run_hourly_debug(site_dir, net_path, target_profile, args.hour, args.demand))
    else:
        report.update(run_daily_profile(site_dir, net_path, target_profile))

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
