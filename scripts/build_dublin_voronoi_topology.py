#!/usr/bin/env python3
"""Build Dublin Voronoi zoning artifacts and topology JSONs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from shapely import MultiPoint, box, voronoi_polygons
from shapely.geometry import mapping


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build true Voronoi zoning artifacts for topology-ready Dublin SCATS sites."
    )
    parser.add_argument(
        "--metadata-csv",
        default="./data/TrafficGeneration/dublin_march_2025/site_metadata.csv",
        help="Processed Dublin site metadata CSV.",
    )
    parser.add_argument(
        "--cells-output",
        default="./data/TrafficGeneration/dublin_march_2025/voronoi_site_cells.geojson",
        help="GeoJSON output path for Voronoi cells keyed by site.",
    )
    parser.add_argument(
        "--adjacency-output",
        default="./data/TrafficGeneration/dublin_march_2025/voronoi_site_adjacency.json",
        help="JSON output path for Voronoi adjacency keyed by site id.",
    )
    parser.add_argument(
        "--topology-output",
        default="./config/dublin_voronoi_topology.json",
        help="Topology JSON output path for the full Dublin Voronoi graph.",
    )
    parser.add_argument(
        "--smoke-topology-output",
        default="./config/dublin_voronoi_smoke_5.json",
        help="Topology JSON output path for the small local smoke subset.",
    )
    parser.add_argument(
        "--smoke-count",
        type=int,
        default=5,
        help="Number of nearby sites to keep in the smoke topology.",
    )
    parser.add_argument(
        "--anchor-site",
        default="95",
        help="Anchor site for the smoke topology subset.",
    )
    parser.add_argument(
        "--retained-column",
        default="retained_for_topology",
        help="Boolean metadata column indicating topology-ready sites.",
    )
    parser.add_argument(
        "--site-column",
        default="site_id",
        help="Metadata site-id column.",
    )
    parser.add_argument(
        "--lat-column",
        default="lat",
        help="Metadata latitude column.",
    )
    parser.add_argument(
        "--long-column",
        default="long",
        help="Metadata longitude column.",
    )
    parser.add_argument(
        "--description-column",
        default="description",
        help="Metadata description column, if present.",
    )
    parser.add_argument(
        "--region-column",
        default="region",
        help="Metadata region column, if present.",
    )
    parser.add_argument(
        "--quality-flag-column",
        default="quality_flag",
        help="Metadata quality-flag column, if present.",
    )
    parser.add_argument(
        "--boundary-padding-deg",
        type=float,
        default=0.02,
        help="Padding in degrees added to the retained-site bounding box before clipping Voronoi cells.",
    )
    parser.add_argument(
        "--port-start",
        type=int,
        default=7000,
        help="Starting TCP port for the full topology JSON.",
    )
    parser.add_argument(
        "--smoke-port-start",
        type=int,
        default=5600,
        help="Starting TCP port for the smoke topology JSON.",
    )
    parser.add_argument(
        "--min-neighbors",
        type=int,
        default=2,
        help="Minimum neighbors per site after topology augmentation.",
    )
    return parser.parse_args()


def normalise_site_id(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip()


def load_topology_ready_sites(args: argparse.Namespace) -> pd.DataFrame:
    metadata = pd.read_csv(args.metadata_csv)
    metadata = metadata.copy()
    metadata[args.site_column] = normalise_site_id(metadata[args.site_column])
    metadata[args.lat_column] = pd.to_numeric(metadata[args.lat_column], errors="coerce")
    metadata[args.long_column] = pd.to_numeric(metadata[args.long_column], errors="coerce")

    retained = metadata[metadata[args.retained_column] == True].copy()
    retained = retained.dropna(subset=[args.lat_column, args.long_column])
    retained = retained.sort_values(args.site_column).reset_index(drop=True)
    if retained.empty:
        raise ValueError("No topology-ready Dublin sites are available for Voronoi generation.")
    return retained


def build_boundary(sites: pd.DataFrame, lat_column: str, long_column: str, padding_deg: float):
    min_lat = sites[lat_column].min() - padding_deg
    max_lat = sites[lat_column].max() + padding_deg
    min_long = sites[long_column].min() - padding_deg
    max_long = sites[long_column].max() + padding_deg
    return box(min_long, min_lat, max_long, max_lat)


def build_voronoi_cells(sites: pd.DataFrame, args: argparse.Namespace):
    points = [tuple(row) for row in sites[[args.long_column, args.lat_column]].to_numpy()]
    geometry = voronoi_polygons(MultiPoint(points), extend_to=build_boundary(sites, args.lat_column, args.long_column, args.boundary_padding_deg), ordered=True)
    boundary = build_boundary(sites, args.lat_column, args.long_column, args.boundary_padding_deg)

    cells = {}
    for site_id, polygon in zip(sites[args.site_column].tolist(), geometry.geoms):
        cells[str(site_id)] = polygon.intersection(boundary)
    return cells, boundary


def build_voronoi_adjacency(cells: dict[str, object]) -> dict[str, list[str]]:
    site_ids = sorted(cells.keys(), key=lambda value: (int(value) if value.isdigit() else value))
    adjacency = {site_id: set() for site_id in site_ids}

    for index, left_id in enumerate(site_ids):
        left_geom = cells[left_id]
        for right_id in site_ids[index + 1 :]:
            right_geom = cells[right_id]
            if not left_geom.touches(right_geom):
                continue

            boundary = left_geom.boundary.intersection(right_geom.boundary)
            if boundary.is_empty:
                continue

            if boundary.geom_type in {"Point", "MultiPoint"}:
                continue

            adjacency[left_id].add(right_id)
            adjacency[right_id].add(left_id)

    return {site_id: sorted(neighbors, key=lambda value: (int(value) if value.isdigit() else value)) for site_id, neighbors in adjacency.items()}


def haversine_distance_km(lat_a: float, long_a: float, lat_b: float, long_b: float) -> float:
    radius_km = 6371.0
    lat_a_rad = np.radians(lat_a)
    lat_b_rad = np.radians(lat_b)
    delta_lat = np.radians(lat_b - lat_a)
    delta_long = np.radians(long_b - long_a)

    hav = (
        np.sin(delta_lat / 2.0) ** 2
        + np.cos(lat_a_rad) * np.cos(lat_b_rad) * np.sin(delta_long / 2.0) ** 2
    )
    return radius_km * (2.0 * np.arcsin(np.sqrt(np.clip(hav, 0.0, 1.0))))


def augment_min_neighbors(adjacency: dict[str, list[str]], sites: pd.DataFrame, args: argparse.Namespace) -> dict[str, list[str]]:
    coords = {
        str(row[args.site_column]): (float(row[args.lat_column]), float(row[args.long_column]))
        for _, row in sites.iterrows()
    }
    augmented = {site_id: set(neighbors) for site_id, neighbors in adjacency.items()}

    for site_id in sorted(augmented.keys(), key=lambda value: (int(value) if value.isdigit() else value)):
        if len(augmented[site_id]) >= args.min_neighbors:
            continue

        lat_a, long_a = coords[site_id]
        candidates = []
        for other_id, (lat_b, long_b) in coords.items():
            if other_id == site_id or other_id in augmented[site_id]:
                continue
            candidates.append((haversine_distance_km(lat_a, long_a, lat_b, long_b), other_id))

        candidates.sort()
        needed = max(0, args.min_neighbors - len(augmented[site_id]))
        for _, other_id in candidates[:needed]:
            augmented[site_id].add(other_id)
            augmented[other_id].add(site_id)

    return {site_id: sorted(neighbors, key=lambda value: (int(value) if value.isdigit() else value)) for site_id, neighbors in augmented.items()}


def build_topology_json(site_ids: list[str], adjacency: dict[str, list[str]], port_start: int) -> dict[str, dict[str, object]]:
    topology = {}
    for index, site_id in enumerate(site_ids):
        topology[str(site_id)] = {
            "id": int(site_id) if str(site_id).isdigit() else str(site_id),
            "ip": "127.0.0.1",
            "port": port_start + index,
            "neighbors": [
                int(neighbor_id) if str(neighbor_id).isdigit() else str(neighbor_id)
                for neighbor_id in adjacency[str(site_id)]
            ],
        }
    return topology


def build_smoke_subset(sites: pd.DataFrame, full_adjacency: dict[str, list[str]], args: argparse.Namespace) -> tuple[list[str], dict[str, list[str]]]:
    site_ids = sites[args.site_column].astype(str)
    if args.anchor_site not in set(site_ids):
        raise ValueError(f"Anchor site {args.anchor_site} is not present in the topology-ready Dublin metadata.")

    anchor = sites[site_ids == args.anchor_site].iloc[0]
    distances = []
    for _, row in sites.iterrows():
        site_id = str(row[args.site_column])
        distance = haversine_distance_km(
            float(anchor[args.lat_column]),
            float(anchor[args.long_column]),
            float(row[args.lat_column]),
            float(row[args.long_column]),
        )
        distances.append((distance, site_id))

    distances.sort(key=lambda item: (item[0], int(item[1]) if item[1].isdigit() else item[1]))
    subset_ids = [site_id for _, site_id in distances[: args.smoke_count]]

    subset_adjacency = {}
    for site_id in subset_ids:
        subset_neighbors = [neighbor for neighbor in full_adjacency[site_id] if neighbor in subset_ids]
        subset_adjacency[site_id] = subset_neighbors

    subset_sites = sites[sites[args.site_column].astype(str).isin(subset_ids)].copy()
    subset_adjacency = augment_min_neighbors(subset_adjacency, subset_sites, args)
    return subset_ids, subset_adjacency


def write_geojson(cells: dict[str, object], sites: pd.DataFrame, boundary, args: argparse.Namespace, output_path: Path) -> None:
    metadata_by_site = {
        str(row[args.site_column]): row
        for _, row in sites.iterrows()
    }
    features = []
    for site_id, polygon in cells.items():
        row = metadata_by_site[site_id]
        properties = {
            "site_id": site_id,
            "lat": float(row[args.lat_column]),
            "long": float(row[args.long_column]),
        }
        for column in [args.description_column, args.region_column, args.quality_flag_column]:
            if column in row.index and pd.notna(row[column]):
                properties[column] = row[column]

        features.append(
            {
                "type": "Feature",
                "geometry": mapping(polygon),
                "properties": properties,
            }
        )

    collection = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "site_count": len(features),
            "boundary_padding_deg": args.boundary_padding_deg,
            "boundary": mapping(boundary),
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(collection, indent=2), encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    sites = load_topology_ready_sites(args)
    cells, boundary = build_voronoi_cells(sites, args)
    adjacency = build_voronoi_adjacency(cells)
    adjacency = augment_min_neighbors(adjacency, sites, args)

    site_ids = sites[args.site_column].astype(str).tolist()
    full_topology = build_topology_json(site_ids, adjacency, args.port_start)
    smoke_site_ids, smoke_adjacency = build_smoke_subset(sites, adjacency, args)
    smoke_topology = build_topology_json(smoke_site_ids, smoke_adjacency, args.smoke_port_start)

    write_geojson(cells, sites, boundary, args, Path(args.cells_output).resolve())
    write_json(Path(args.adjacency_output).resolve(), adjacency)
    write_json(Path(args.topology_output).resolve(), full_topology)
    write_json(Path(args.smoke_topology_output).resolve(), smoke_topology)

    print(f"Built Dublin Voronoi cells for {len(site_ids)} topology-ready sites.")
    print(f"Full topology output: {Path(args.topology_output).resolve()}")
    print(f"Smoke topology output: {Path(args.smoke_topology_output).resolve()}")


if __name__ == "__main__":
    main()
