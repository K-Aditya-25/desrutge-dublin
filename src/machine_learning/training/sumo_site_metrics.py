from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path


def detector_output_files(site_dir: str | Path) -> list[str]:
    site_path = Path(site_dir)
    tree = ET.parse(site_path / "detectors.add.xml")
    root = tree.getroot()
    files = []
    for induction_loop in root.findall("inductionLoop"):
        output_file = induction_loop.get("file")
        if output_file:
            files.append(output_file)
    return files


def parse_detector_hourly_counts(detector_xml: str | Path) -> list[int]:
    hourly = [0] * 24
    tree = ET.parse(detector_xml)
    root = tree.getroot()
    for interval in root.findall("interval"):
        begin = float(interval.get("begin", "0"))
        hour = min(int(begin / 3600), 23)
        hourly[hour] += int(float(interval.get("nVehContrib", "0")))
    return hourly


def combine_hourly_profiles(per_detector_profiles: list[list[int]]) -> list[int]:
    combined = [0] * 24
    for profile in per_detector_profiles:
        combined = [left + right for left, right in zip(combined, profile)]
    return combined


def collect_site_detector_profiles(site_dir: str | Path) -> tuple[list[list[int]], list[int]]:
    site_path = Path(site_dir)
    per_detector = []
    for relative_name in detector_output_files(site_path):
        per_detector.append(parse_detector_hourly_counts(site_path / relative_name))
    return per_detector, combine_hourly_profiles(per_detector)


def profile_mean(profile: list[int | float]) -> float:
    if not profile:
        return 0.0
    return float(sum(profile)) / float(len(profile))


def compute_profile_metrics(target_profile: list[int], simulated_profile: list[int]) -> dict:
    if len(target_profile) != 24 or len(simulated_profile) != 24:
        raise ValueError("Expected both target and simulated profiles to have exactly 24 hourly values.")

    hourly_error = [simulated - target for target, simulated in zip(target_profile, simulated_profile)]
    hourly_absolute_error = [abs(value) for value in hourly_error]
    squared_error = [value * value for value in hourly_error]

    return {
        "hourly_error": hourly_error,
        "hourly_absolute_error": hourly_absolute_error,
        "mae": sum(hourly_absolute_error) / 24.0,
        "rmse": math.sqrt(sum(squared_error) / 24.0),
        "total_target": sum(target_profile),
        "total_simulated": sum(simulated_profile),
        "daily_mean_target": profile_mean(target_profile),
        "daily_mean_simulated": profile_mean(simulated_profile),
    }
