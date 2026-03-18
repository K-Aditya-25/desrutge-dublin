#!/usr/bin/env python3
"""Validate one SUMO site folder for DesRUTGe."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


REQUIRED_FILES = ["sim.sumocfg", "miniTAZ.xml", "detectors.add.xml", "od_file.od"]
OPTIONAL_RUNTIME_FILES = ["osm.net.xml", "routes.rou.xml", "trips.xml", "trips_via.xml"]
REQUIRED_COMMANDS = ["od2trips", "duarouter", "sumo"]
PLACEHOLDER_TOKENS = ["REPLACE_SOURCE_EDGE", "REPLACE_SINK_EDGE", "REPLACE_LANE_ID"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a Dublin SUMO site folder.")
    parser.add_argument("--site-dir", required=True, help="Path to the site SUMO folder.")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run od2trips, duarouter, and sumo after validation.",
    )
    return parser.parse_args()


def ensure_commands() -> None:
    missing = [command for command in REQUIRED_COMMANDS if shutil.which(command) is None]
    if missing:
        raise RuntimeError(f"Missing required SUMO commands: {missing}")


def validate_files(site_dir: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not (site_dir / name).exists()]
    if missing:
        raise RuntimeError(f"Missing required site files: {missing}")

    net_path = resolve_net_path(site_dir)
    if not net_path.exists():
        raise RuntimeError(f"Missing configured SUMO net-file: {net_path.name}")


def resolve_net_path(site_dir: Path) -> Path:
    sim_cfg = site_dir / "sim.sumocfg"
    tree = ET.parse(sim_cfg)
    root = tree.getroot()
    net_node = root.find("./input/net-file")
    if net_node is None:
        raise RuntimeError("sim.sumocfg is missing <input>/<net-file>.")

    net_value = net_node.get("value")
    if not net_value:
        raise RuntimeError("sim.sumocfg has an empty <net-file value=...>.")

    return site_dir / net_value


def validate_placeholders(site_dir: Path) -> None:
    placeholder_hits = []
    for relative_path in ["miniTAZ.xml", "detectors.add.xml"]:
        path = site_dir / relative_path
        contents = path.read_text(encoding="utf-8")
        for token in PLACEHOLDER_TOKENS:
            if token in contents:
                placeholder_hits.append((relative_path, token))

    if placeholder_hits:
        details = ", ".join(f"{path}:{token}" for path, token in placeholder_hits)
        raise RuntimeError(
            "The site folder still contains placeholder values that must be replaced in netedit/by hand before SUMO can run: "
            + details
        )


def run_commands(site_dir: Path) -> None:
    net_path = resolve_net_path(site_dir)
    subprocess.run(
        ["od2trips", "-n", "miniTAZ.xml", "-d", "od_file.od", "-o", "trips.xml"],
        cwd=site_dir,
        check=True,
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
    )
    subprocess.run(["sumo", "-c", "sim.sumocfg", "--no-warnings"], cwd=site_dir, check=True)


def main() -> None:
    args = parse_args()
    site_dir = Path(args.site_dir).resolve()
    ensure_commands()
    validate_files(site_dir)
    validate_placeholders(site_dir)

    present_optional = [name for name in OPTIONAL_RUNTIME_FILES if (site_dir / name).exists()]
    print(f"Site folder: {site_dir}")
    print(f"Optional runtime files already present: {present_optional}")

    if args.run:
        run_commands(site_dir)
        print("SUMO validation run completed.")
    else:
        print("Validation checks passed. Re-run with --run to execute od2trips, duarouter, and sumo.")


if __name__ == "__main__":
    main()
