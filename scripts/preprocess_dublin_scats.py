#!/usr/bin/env python3
"""Prepare Dublin SCATS hourly data for DesRUTGe."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


SITE_ID_COLUMN = "site_id"
HOUR_COLUMNS = [f"h{hour:02d}" for hour in range(24)]


@dataclass
class OutputPaths:
    output_dir: Path
    compatibility_csv: Path
    long_targets_csv: Path
    site_date_hour_csv: Path
    site_metadata_csv: Path
    summary_json: Path
    topology_json: Path | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Dublin SCATS hourly traffic data into DesRUTGe-compatible site profiles."
    )
    parser.add_argument("--hourly-data", required=True, help="Path to Dublin SCATS hourly counts CSV.")
    parser.add_argument("--site-metadata", required=True, help="Path to Dublin SCATS site metadata CSV.")
    parser.add_argument(
        "--output-dir",
        default="./data/TrafficGeneration/dublin",
        help="Directory for generated artifacts.",
    )
    parser.add_argument(
        "--mode",
        choices=["compatibility", "paper-faithful"],
        default="compatibility",
        help="Compatibility writes repo-facing outputs; paper-faithful also keeps richer intermediates.",
    )
    parser.add_argument("--end-time-column", default="End Time", help="Hourly counts timestamp column.")
    parser.add_argument("--site-column", default="Site", help="Hourly counts site identifier column.")
    parser.add_argument("--detector-column", default="Detector", help="Hourly counts detector identifier column.")
    parser.add_argument("--volume-column", default="Sum volume", help="Hourly counts traffic volume column.")
    parser.add_argument("--region-column", default="Region", help="Shared region column name.")
    parser.add_argument("--metadata-site-column", default="SiteID", help="Site metadata site identifier column.")
    parser.add_argument(
        "--metadata-site-description-column",
        default="Site_Description_Cap",
        help="Site metadata descriptive label column.",
    )
    parser.add_argument("--metadata-lat-column", default="Lat", help="Site metadata latitude column.")
    parser.add_argument("--metadata-long-column", default="Long", help="Site metadata longitude column.")
    parser.add_argument(
        "--timestamp-format",
        default=None,
        help="Optional explicit datetime format string, for example %%Y%%m%%d%%H%%M%%S.",
    )
    parser.add_argument(
        "--dayfirst",
        action="store_true",
        help="Parse timestamps using day-first ordering. Recommended for Dublin council exports.",
    )
    parser.add_argument(
        "--site-filter",
        nargs="*",
        default=None,
        help="Optional explicit list of site IDs to keep.",
    )
    parser.add_argument(
        "--min-observed-hours",
        type=int,
        default=24,
        help="Minimum number of observed hourly buckets required to keep a site.",
    )
    parser.add_argument(
        "--min-coverage-ratio",
        type=float,
        default=0.5,
        help="Minimum observed/expected hourly coverage ratio required to keep a site.",
    )
    parser.add_argument(
        "--topology-output",
        default=None,
        help="Optional path to write a geographic-neighbor topology JSON for the retained sites.",
    )
    parser.add_argument(
        "--topology-port-start",
        type=int,
        default=5004,
        help="Starting TCP port for generated topology nodes.",
    )
    parser.add_argument(
        "--topology-neighbors",
        type=int,
        default=3,
        help="Number of nearest geographic neighbors per site when generating topology.",
    )
    return parser.parse_args()


def validate_columns(df: pd.DataFrame, required_columns: Iterable[str], label: str) -> None:
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def normalise_site_id(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip()


def build_output_paths(args: argparse.Namespace) -> OutputPaths:
    output_dir = Path(args.output_dir).resolve()
    topology_json = Path(args.topology_output).resolve() if args.topology_output else None
    return OutputPaths(
        output_dir=output_dir,
        compatibility_csv=output_dir / "detector_data.csv",
        long_targets_csv=output_dir / "site_hourly_targets_long.csv",
        site_date_hour_csv=output_dir / "site_date_hour_totals.csv",
        site_metadata_csv=output_dir / "site_metadata.csv",
        summary_json=output_dir / "preprocessing_summary.json",
        topology_json=topology_json,
    )


def load_hourly_counts(args: argparse.Namespace) -> pd.DataFrame:
    hourly_df = pd.read_csv(
        args.hourly_data,
        usecols=[
            args.end_time_column,
            args.region_column,
            args.site_column,
            args.detector_column,
            args.volume_column,
        ],
        dtype={
            args.end_time_column: "string",
            args.region_column: "string",
            args.site_column: "string",
            args.detector_column: "string",
        },
    )
    validate_columns(
        hourly_df,
        [args.end_time_column, args.site_column, args.detector_column, args.volume_column, args.region_column],
        "Hourly SCATS data",
    )

    hourly_df = hourly_df.copy()
    hourly_df[args.site_column] = normalise_site_id(hourly_df[args.site_column])
    hourly_df[args.detector_column] = hourly_df[args.detector_column].astype(str).str.strip()
    hourly_df[args.volume_column] = pd.to_numeric(hourly_df[args.volume_column], errors="coerce")
    hourly_df = hourly_df.dropna(subset=[args.volume_column])

    raw_timestamps = hourly_df[args.end_time_column].astype("string").str.strip()
    timestamp_format = args.timestamp_format
    if timestamp_format is None:
        if raw_timestamps.str.fullmatch(r"\d{14}").all():
            timestamp_format = "%Y%m%d%H%M%S"
        elif raw_timestamps.str.fullmatch(r"\d{12}").all():
            timestamp_format = "%Y%m%d%H%M"

    if timestamp_format is not None:
        hourly_df["timestamp"] = pd.to_datetime(raw_timestamps, errors="coerce", format=timestamp_format)
    else:
        hourly_df["timestamp"] = pd.to_datetime(
            raw_timestamps,
            errors="coerce",
            dayfirst=args.dayfirst,
        )
    hourly_df = hourly_df.dropna(subset=["timestamp"])
    hourly_df["date"] = hourly_df["timestamp"].dt.date.astype(str)
    hourly_df["hour"] = hourly_df["timestamp"].dt.hour.astype(int)
    hourly_df["volume"] = hourly_df[args.volume_column].clip(lower=0)

    if args.site_filter:
        site_filter = {str(site).strip() for site in args.site_filter}
        hourly_df = hourly_df[hourly_df[args.site_column].isin(site_filter)]

    if hourly_df.empty:
        raise ValueError("No hourly SCATS rows remain after parsing and filtering.")

    return hourly_df


def load_site_metadata(args: argparse.Namespace) -> pd.DataFrame:
    metadata_df = pd.read_csv(
        args.site_metadata,
        usecols=[
            args.metadata_site_column,
            args.region_column,
            args.metadata_site_description_column,
            args.metadata_lat_column,
            args.metadata_long_column,
        ],
        dtype={
            args.metadata_site_column: "string",
            args.region_column: "string",
            args.metadata_site_description_column: "string",
        },
    )
    validate_columns(
        metadata_df,
        [
            args.metadata_site_column,
            args.region_column,
            args.metadata_site_description_column,
            args.metadata_lat_column,
            args.metadata_long_column,
        ],
        "SCATS site metadata",
    )

    metadata_df = metadata_df.copy()
    metadata_df[args.metadata_site_column] = normalise_site_id(metadata_df[args.metadata_site_column])
    metadata_df[args.metadata_lat_column] = pd.to_numeric(metadata_df[args.metadata_lat_column], errors="coerce")
    metadata_df[args.metadata_long_column] = pd.to_numeric(metadata_df[args.metadata_long_column], errors="coerce")
    metadata_df = metadata_df.drop_duplicates(subset=[args.metadata_site_column], keep="first")
    return metadata_df


def aggregate_site_hourly(hourly_df: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    return (
        hourly_df.groupby([args.site_column, args.region_column, "date", "hour"], as_index=False)["volume"]
        .sum()
        .rename(
            columns={
                args.site_column: SITE_ID_COLUMN,
                args.region_column: "region",
                "volume": "site_hour_volume",
            }
        )
    )


def summarise_site_profiles(
    site_date_hour_totals: pd.DataFrame, metadata_df: pd.DataFrame, args: argparse.Namespace
) -> tuple[pd.DataFrame, pd.DataFrame]:
    global_dates = site_date_hour_totals["date"].nunique()
    expected_hours = global_dates * 24 if global_dates else 0

    site_regions = (
        site_date_hour_totals.groupby(SITE_ID_COLUMN)["region"]
        .agg(lambda values: values.mode().iat[0] if not values.mode().empty else values.iloc[0])
        .rename("region_observed")
        .reset_index()
    )

    profile_long = (
        site_date_hour_totals.groupby([SITE_ID_COLUMN, "hour"], as_index=False)["site_hour_volume"]
        .mean()
        .rename(columns={"site_hour_volume": "target_cars_per_hour"})
        .merge(site_regions, on=SITE_ID_COLUMN, how="left")
    )

    profile_wide = (
        profile_long.assign(hour_column=profile_long["hour"].map(lambda hour: f"h{hour:02d}"))
        .pivot(index=SITE_ID_COLUMN, columns="hour_column", values="target_cars_per_hour")
        .reindex(columns=HOUR_COLUMNS)
        .reset_index()
    )

    observed_hours = (
        site_date_hour_totals.groupby(SITE_ID_COLUMN)
        .size()
        .rename("observed_hours")
        .reset_index()
    )
    observed_dates = (
        site_date_hour_totals.groupby(SITE_ID_COLUMN)["date"]
        .nunique()
        .rename("observed_dates")
        .reset_index()
    )
    detector_counts = (
        site_date_hour_totals.groupby(SITE_ID_COLUMN)["region"]
        .size()
        .rename("site_hour_records")
        .reset_index()
    )

    metadata_columns = {
        args.metadata_site_column: SITE_ID_COLUMN,
        args.metadata_site_description_column: "site_description",
        args.region_column: "region_metadata",
        args.metadata_lat_column: "lat",
        args.metadata_long_column: "long",
    }
    site_summary = (
        metadata_df.rename(columns=metadata_columns)[list(metadata_columns.values())]
        .merge(site_regions, on=SITE_ID_COLUMN, how="outer")
        .merge(observed_hours, on=SITE_ID_COLUMN, how="outer")
        .merge(observed_dates, on=SITE_ID_COLUMN, how="outer")
        .merge(detector_counts, on=SITE_ID_COLUMN, how="outer")
        .merge(profile_wide, on=SITE_ID_COLUMN, how="outer")
    )

    site_summary["expected_hours"] = expected_hours
    site_summary["coverage_ratio"] = np.where(
        expected_hours > 0,
        site_summary["observed_hours"].fillna(0) / expected_hours,
        np.nan,
    )
    site_summary["has_all_24_hours"] = site_summary[HOUR_COLUMNS].notna().all(axis=1)
    site_summary["missing_coordinates"] = site_summary[["lat", "long"]].isna().any(axis=1)
    site_summary["quality_flag"] = "ok"
    site_summary.loc[site_summary["coverage_ratio"].fillna(0) < args.min_coverage_ratio, "quality_flag"] = "low_coverage"
    site_summary.loc[site_summary["observed_hours"].fillna(0) < args.min_observed_hours, "quality_flag"] = "low_observed_hours"
    site_summary.loc[~site_summary["has_all_24_hours"], "quality_flag"] = "missing_hour_targets"
    site_summary.loc[site_summary["missing_coordinates"], "quality_flag"] = "missing_coordinates"

    retained = site_summary[
        (site_summary["observed_hours"].fillna(0) >= args.min_observed_hours)
        & (site_summary["coverage_ratio"].fillna(0) >= args.min_coverage_ratio)
        & site_summary["has_all_24_hours"]
    ].copy()

    retained["retained_for_repo"] = True
    site_summary["retained_for_repo"] = site_summary[SITE_ID_COLUMN].isin(retained[SITE_ID_COLUMN])
    site_summary["retained_for_topology"] = site_summary["retained_for_repo"] & ~site_summary["missing_coordinates"]
    return profile_long, site_summary.sort_values(SITE_ID_COLUMN)


def create_compatibility_csv(site_summary: pd.DataFrame) -> pd.DataFrame:
    compatible = site_summary[site_summary["retained_for_repo"]].copy()
    compatibility_columns = [SITE_ID_COLUMN] + HOUR_COLUMNS
    compatibility_df = compatible[compatibility_columns].sort_values(SITE_ID_COLUMN).reset_index(drop=True)
    for column in HOUR_COLUMNS:
        compatibility_df[column] = compatibility_df[column].astype(float).round(3)
    return compatibility_df


def haversine_distance_matrix(latitudes: np.ndarray, longitudes: np.ndarray) -> np.ndarray:
    radius_km = 6371.0
    lat_rad = np.radians(latitudes)
    long_rad = np.radians(longitudes)

    lat_diff = lat_rad[:, None] - lat_rad[None, :]
    long_diff = long_rad[:, None] - long_rad[None, :]

    a = (
        np.sin(lat_diff / 2.0) ** 2
        + np.cos(lat_rad[:, None]) * np.cos(lat_rad[None, :]) * np.sin(long_diff / 2.0) ** 2
    )
    c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    return radius_km * c


def build_geographic_topology(
    compatibility_df: pd.DataFrame,
    site_summary: pd.DataFrame,
    topology_neighbors: int,
    port_start: int,
) -> dict[str, dict[str, object]]:
    topology_sites = compatibility_df[SITE_ID_COLUMN].tolist()
    topology_metadata = (
        site_summary[site_summary[SITE_ID_COLUMN].isin(topology_sites)]
        .set_index(SITE_ID_COLUMN)
        .loc[topology_sites]
    )
    if topology_metadata[["lat", "long"]].isna().any().any():
        missing = topology_metadata[topology_metadata[["lat", "long"]].isna().any(axis=1)].index.tolist()
        raise ValueError(f"Cannot generate topology because these sites are missing coordinates: {missing}")

    latitudes = topology_metadata["lat"].to_numpy(dtype=float)
    longitudes = topology_metadata["long"].to_numpy(dtype=float)
    distances = haversine_distance_matrix(latitudes, longitudes)

    topology: dict[str, dict[str, object]] = {}
    for index, site_id in enumerate(topology_sites):
        sorted_indices = np.argsort(distances[index])
        neighbor_indices = [i for i in sorted_indices if i != index][:topology_neighbors]
        topology[str(site_id)] = {
            "id": int(site_id) if str(site_id).isdigit() else str(site_id),
            "ip": "127.0.0.1",
            "port": port_start + index,
            "neighbors": [
                int(topology_sites[neighbor_index])
                if str(topology_sites[neighbor_index]).isdigit()
                else str(topology_sites[neighbor_index])
                for neighbor_index in neighbor_indices
            ],
        }
    return topology


def write_outputs(
    paths: OutputPaths,
    compatibility_df: pd.DataFrame,
    profile_long: pd.DataFrame,
    site_date_hour_totals: pd.DataFrame,
    site_summary: pd.DataFrame,
    args: argparse.Namespace,
) -> dict[str, object]:
    paths.output_dir.mkdir(parents=True, exist_ok=True)

    compatibility_df.to_csv(paths.compatibility_csv, index=False)
    site_summary.to_csv(paths.site_metadata_csv, index=False)

    if args.mode == "paper-faithful":
        profile_long.sort_values([SITE_ID_COLUMN, "hour"]).to_csv(paths.long_targets_csv, index=False)
        site_date_hour_totals.sort_values([SITE_ID_COLUMN, "date", "hour"]).to_csv(paths.site_date_hour_csv, index=False)

    summary = {
        "mode": args.mode,
        "hourly_data": str(Path(args.hourly_data).resolve()),
        "site_metadata": str(Path(args.site_metadata).resolve()),
        "output_dir": str(paths.output_dir),
        "retained_sites": int(len(compatibility_df)),
        "rejected_sites": int((~site_summary["retained_for_repo"]).sum()),
        "compatibility_csv": str(paths.compatibility_csv),
        "site_metadata_csv": str(paths.site_metadata_csv),
        "paper_faithful_long_targets_csv": str(paths.long_targets_csv) if args.mode == "paper-faithful" else None,
        "paper_faithful_site_date_hour_csv": str(paths.site_date_hour_csv) if args.mode == "paper-faithful" else None,
        "quality_flag_counts": site_summary["quality_flag"].value_counts(dropna=False).to_dict(),
        "site_ids": compatibility_df[SITE_ID_COLUMN].tolist(),
        "topology_ready_sites": int(site_summary["retained_for_topology"].sum()),
    }

    if paths.topology_json:
        topology = build_geographic_topology(
            compatibility_df=compatibility_df,
            site_summary=site_summary,
            topology_neighbors=args.topology_neighbors,
            port_start=args.topology_port_start,
        )
        paths.topology_json.parent.mkdir(parents=True, exist_ok=True)
        with paths.topology_json.open("w", encoding="utf-8") as handle:
            json.dump(topology, handle, indent=4)
        summary["topology_json"] = str(paths.topology_json)

    with paths.summary_json.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    return summary


def main() -> None:
    args = parse_args()
    paths = build_output_paths(args)

    hourly_df = load_hourly_counts(args)
    metadata_df = load_site_metadata(args)
    site_date_hour_totals = aggregate_site_hourly(hourly_df, args)
    profile_long, site_summary = summarise_site_profiles(site_date_hour_totals, metadata_df, args)
    compatibility_df = create_compatibility_csv(site_summary)

    if compatibility_df.empty:
        raise ValueError("No sites passed validation; widen the filters or inspect the generated metadata report.")

    summary = write_outputs(
        paths=paths,
        compatibility_df=compatibility_df,
        profile_long=profile_long,
        site_date_hour_totals=site_date_hour_totals,
        site_summary=site_summary,
        args=args,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
