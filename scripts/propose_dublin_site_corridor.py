#!/usr/bin/env python3
"""Propose a drivable SUMO corridor for one Dublin SCATS site."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path


def ensure_sumo_tools_importable() -> None:
    candidates = []
    sumo_home = os.environ.get("SUMO_HOME")
    if sumo_home:
        candidates.append(Path(sumo_home) / "tools")
    candidates.extend(
        [
            Path("/usr/share/sumo/tools"),
            Path("/opt/homebrew/share/sumo/tools"),
            Path("/usr/local/share/sumo/tools"),
        ]
    )

    for candidate in candidates:
        if (candidate / "sumolib").exists():
            sys.path.insert(0, str(candidate))
            return

    raise RuntimeError(
        "Could not locate SUMO Python tools. Set SUMO_HOME or install SUMO with sumolib available."
    )


ensure_sumo_tools_importable()

import sumolib  # noqa: E402


SIMCFG_TEMPLATE = """<configuration>
    <input>
        <net-file value="{net_file}"/>
        <additional-files value="detectors.add.xml"/>
        <route-files value="routes.rou.xml"/>
    </input>

    <time>
        <begin value="0"/>
    </time>

    <processing>
        <time-to-teleport value="300"/>
    </processing>
</configuration>
"""


DETECTORS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    <!-- Auto-proposed detector corridor for site {site_id}; score={score:.2f}; site_distance_m={distance:.2f}. -->
    <inductionLoop id="site_{site_id}_a" lane="{lane_id}" pos="{pos:.2f}" period="900.00" file="AM_{site_id}_a.xml" friendlyPos="1"/>
</additional>
"""


TAZ_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    <!-- Auto-proposed corridor for site {site_id}; source={source_edge}; detector={detector_edge}; sink={sink_edge}. -->
    <taz id="taz" color="blue">
        <tazSource id="{source_edge}" weight="1.00"/>
        <tazSink id="{sink_edge}" weight="1.00"/>
    </taz>
</additional>
"""


OD_TEMPLATE = """$OR;D2
0.00 1.00
1.0
taz taz 100
"""


README_TEMPLATE = """# Dublin SUMO Scenario for Site {site_id}

This folder contains the first-pass Dublin SUMO assets for SCATS site `{site_id}` generated from the reusable corridor proposer.

## Site

- `site_id`: {site_id}
- `description`: {description}
- `region`: {region}
- `lat`: {lat}
- `long`: {lon}

## Active SUMO Assets

- `net-file`: `{net_file}`
- `source edge`: `{source_edge}`
- `detector lane`: `{detector_lane}`
- `sink edge`: `{sink_edge}`
- `proposal score`: `{score:.2f}`
- `detector distance to site marker`: `{distance:.2f}` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/{site_id} --run`
"""

PASSENGER_CLASSES = ("passenger", "private")
EXCLUDED_TYPE_TOKENS = ("pedestrian", "rail", "tram", "subway", "light_rail", "bicycle", "cycleway", "footway")


@dataclass
class SiteInfo:
    site_id: str
    description: str
    region: str
    lat: float
    lon: float
    x: float
    y: float


@dataclass
class CandidateTriple:
    source_edge: str
    detector_edge: str
    sink_edge: str
    source_hops: int
    sink_hops: int
    route_edges: list[str]
    route_cost: float
    route_length_m: float
    route_edge_count: int
    detector_distance_m: float
    detector_lane: str
    detector_pos: float
    detector_name: str
    source_name: str
    sink_name: str
    street_continuity: float
    heading_continuity: float
    simplicity: float
    score: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score candidate source/detector/sink triples for one Dublin SCATS site on a SUMO net."
    )
    parser.add_argument("--site-id", required=True, help="Dublin SCATS site id.")
    parser.add_argument("--site-dir", required=True, help="Target SUMO site folder.")
    parser.add_argument(
        "--site-metadata",
        default="./data/TrafficGeneration/dublin_march_2025/site_metadata.csv",
        help="CSV with site metadata and coordinates.",
    )
    parser.add_argument("--net-file", required=True, help="Relevant SUMO net file for corridor search.")
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of ranked candidates to keep in the report.",
    )
    parser.add_argument(
        "--detector-edge-limit",
        type=int,
        default=18,
        help="Max nearest detector-edge candidates to explore.",
    )
    parser.add_argument(
        "--max-detector-distance",
        type=float,
        default=150.0,
        help="Preferred max detector-edge distance in meters before falling back to the nearest edges.",
    )
    parser.add_argument(
        "--min-detector-edge-length",
        type=float,
        default=6.0,
        help="Minimum drivable detector-edge length in meters.",
    )
    parser.add_argument(
        "--min-endpoint-edge-length",
        type=float,
        default=2.0,
        help="Minimum drivable source/sink edge length in meters.",
    )
    parser.add_argument(
        "--manual-review-threshold",
        type=float,
        default=60.0,
        help="Minimum score required before writing detector/TAZ assets.",
    )
    parser.add_argument(
        "--link-net",
        action="store_true",
        help="Create a symlink to --net-file inside --site-dir when writing assets.",
    )
    parser.add_argument(
        "--write-assets",
        action="store_true",
        help="Write detectors.add.xml, miniTAZ.xml, sim.sumocfg, and od_file.od if a reliable candidate is found.",
    )
    return parser.parse_args()


def load_site_info(metadata_path: Path, site_id: str, net_path: Path) -> SiteInfo:
    target = str(site_id).strip()
    with metadata_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if str(row["site_id"]).strip() != target:
                continue
            lat = float(row["lat"])
            lon = float(row["long"])
            x, y = site_lonlat_to_net_xy(net_path, lon=lon, lat=lat)
            return SiteInfo(
                site_id=target,
                description=row.get("site_description", ""),
                region=row.get("region_metadata", ""),
                lat=lat,
                lon=lon,
                x=x,
                y=y,
            )
    raise RuntimeError(f"Site {site_id} was not found in {metadata_path}.")


def site_lonlat_to_net_xy(net_path: Path, lon: float, lat: float) -> tuple[float, float]:
    location = ET.parse(net_path).getroot().find("location")
    if location is None:
        raise RuntimeError(f"{net_path} is missing the SUMO <location> element.")

    offset = location.get("netOffset")
    proj_parameter = location.get("projParameter")
    if not offset or not proj_parameter:
        raise RuntimeError(f"{net_path} is missing netOffset or projParameter in <location>.")

    zone_match = re.search(r"\+zone=(\d+)", proj_parameter)
    if "+proj=utm" not in proj_parameter or zone_match is None:
        raise RuntimeError(
            f"Only UTM SUMO nets are supported by the heuristic fallback right now. projParameter={proj_parameter!r}"
        )

    zone = int(zone_match.group(1))
    projected_x, projected_y = latlon_to_utm_wgs84(lat=lat, lon=lon, zone=zone)
    offset_x, offset_y = [float(value) for value in offset.split(",")]
    return projected_x + offset_x, projected_y + offset_y


def latlon_to_utm_wgs84(lat: float, lon: float, zone: int) -> tuple[float, float]:
    a = 6378137.0
    flattening = 1 / 298.257223563
    e_sq = flattening * (2 - flattening)
    e_prime_sq = e_sq / (1 - e_sq)
    k0 = 0.9996

    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    lon_origin = math.radians((zone - 1) * 6 - 180 + 3)

    sin_lat = math.sin(lat_rad)
    cos_lat = math.cos(lat_rad)
    tan_lat = math.tan(lat_rad)

    n = a / math.sqrt(1 - e_sq * sin_lat * sin_lat)
    t = tan_lat * tan_lat
    c = e_prime_sq * cos_lat * cos_lat
    a_term = cos_lat * (lon_rad - lon_origin)

    m = a * (
        (1 - e_sq / 4 - 3 * e_sq**2 / 64 - 5 * e_sq**3 / 256) * lat_rad
        - (3 * e_sq / 8 + 3 * e_sq**2 / 32 + 45 * e_sq**3 / 1024) * math.sin(2 * lat_rad)
        + (15 * e_sq**2 / 256 + 45 * e_sq**3 / 1024) * math.sin(4 * lat_rad)
        - (35 * e_sq**3 / 3072) * math.sin(6 * lat_rad)
    )

    easting = k0 * n * (
        a_term
        + (1 - t + c) * a_term**3 / 6
        + (5 - 18 * t + t**2 + 72 * c - 58 * e_prime_sq) * a_term**5 / 120
    ) + 500000.0

    northing = k0 * (
        m
        + n
        * tan_lat
        * (
            a_term**2 / 2
            + (5 - t + 9 * c + 4 * c**2) * a_term**4 / 24
            + (61 - 58 * t + t**2 + 600 * c - 330 * e_prime_sq) * a_term**6 / 720
        )
    )

    if lat < 0:
        northing += 10000000.0

    return easting, northing


def edge_name(edge) -> str:
    name = (edge.getName() or "").strip()
    return name


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def edge_heading_degrees(edge) -> float:
    shape = edge.getRawShape()
    if len(shape) < 2:
        return 0.0
    start_x, start_y = shape[0]
    end_x, end_y = shape[-1]
    return math.degrees(math.atan2(end_y - start_y, end_x - start_x))


def heading_similarity(a: float, b: float) -> float:
    delta = abs((a - b + 180.0) % 360.0 - 180.0)
    return max(0.0, 1.0 - delta / 180.0)


def point_segment_distance(point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]) -> float:
    px, py = point
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0.0 and dy == 0.0:
        return math.hypot(px - x1, py - y1)

    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    nearest_x = x1 + t * dx
    nearest_y = y1 + t * dy
    return math.hypot(px - nearest_x, py - nearest_y)


def point_edge_distance(edge, x: float, y: float) -> float:
    shape = edge.getRawShape()
    if not shape:
        return float("inf")
    if len(shape) == 1:
        return math.hypot(x - shape[0][0], y - shape[0][1])
    return min(
        point_segment_distance((x, y), shape[index], shape[index + 1])
        for index in range(len(shape) - 1)
    )


def passenger_lane(edge):
    for lane in edge.getLanes():
        if any(lane.allows(vehicle_class) for vehicle_class in PASSENGER_CLASSES):
            return lane
    return None


def is_viable_drivable_edge(edge, min_edge_length: float) -> bool:
    if edge.getID().startswith(":"):
        return False
    if edge.getLength() < min_edge_length:
        return False
    edge_type = (edge.getType() or "").lower()
    if any(token in edge_type for token in EXCLUDED_TYPE_TOKENS):
        return False
    return passenger_lane(edge) is not None


def incoming_edges(edge) -> list:
    edges = edge.getIncoming()
    if isinstance(edges, dict):
        return list(edges.keys())
    return list(edges)


def outgoing_edges(edge) -> list:
    edges = edge.getOutgoing()
    if isinstance(edges, dict):
        return list(edges.keys())
    return list(edges)


def collect_directional_edges(start_edge, direction: str, min_edge_length: float, max_hops: int = 3) -> list[tuple[object, int]]:
    neighbor_fn = incoming_edges if direction == "upstream" else outgoing_edges
    results = []
    seen = {start_edge.getID()}
    frontier = deque([(start_edge, 0)])

    while frontier:
        edge, hops = frontier.popleft()
        if hops >= max_hops:
            continue
        for neighbor in neighbor_fn(edge):
            if neighbor.getID() in seen:
                continue
            seen.add(neighbor.getID())
            next_hops = hops + 1
            frontier.append((neighbor, next_hops))
            if is_viable_drivable_edge(neighbor, min_edge_length):
                results.append((neighbor, next_hops))

    return results


def candidate_detector_edges(net, site: SiteInfo, min_edge_length: float, limit: int, max_distance: float) -> list[tuple[object, float]]:
    all_edges = []
    for edge in net.getEdges():
        if not is_viable_drivable_edge(edge, min_edge_length):
            continue
        distance = point_edge_distance(edge, site.x, site.y)
        all_edges.append((edge, distance))

    all_edges.sort(key=lambda item: (item[1], -item[0].getLength()))
    nearby = [item for item in all_edges if item[1] <= max_distance]
    if nearby:
        return nearby[:limit]
    return all_edges[:limit]


def compute_detector_pos(lane_length: float) -> float:
    if lane_length <= 2.0:
        return 1.0
    return min(25.0, max(4.5, lane_length / 2.0))


def street_continuity(route_edges: list, detector_edge_id: str) -> float:
    if not route_edges:
        return 0.0
    names = [normalize_name(edge_name(edge)) for edge in route_edges]
    detector_index = next(index for index, edge in enumerate(route_edges) if edge.getID() == detector_edge_id)
    detector_name = names[detector_index]
    if not detector_name:
        return 0.0

    score = 0.0
    if detector_index > 0 and names[detector_index - 1] == detector_name:
        score += 0.30
    if detector_index < len(route_edges) - 1 and names[detector_index + 1] == detector_name:
        score += 0.30
    same_name_ratio = sum(1 for name in names if name == detector_name) / len(names)
    score += 0.40 * same_name_ratio
    return min(1.0, score)


def route_heading_continuity(route_edges: list, detector_edge_id: str) -> float:
    if not route_edges:
        return 0.0
    detector_index = next(index for index, edge in enumerate(route_edges) if edge.getID() == detector_edge_id)
    detector_heading = edge_heading_degrees(route_edges[detector_index])
    similarities = []
    if detector_index > 0:
        similarities.append(heading_similarity(edge_heading_degrees(route_edges[detector_index - 1]), detector_heading))
    if detector_index < len(route_edges) - 1:
        similarities.append(heading_similarity(detector_heading, edge_heading_degrees(route_edges[detector_index + 1])))
    if not similarities:
        return 0.0
    return sum(similarities) / len(similarities)


def route_simplicity(route_edges: list) -> float:
    if not route_edges:
        return 0.0
    return max(0.0, 1.0 - max(0, len(route_edges) - 3) / 6.0)


def score_triple(route_edges: list, detector_edge_id: str, detector_distance_m: float) -> tuple[float, float, float, float]:
    proximity = max(0.0, 1.0 - min(detector_distance_m, 200.0) / 200.0)
    continuity = street_continuity(route_edges, detector_edge_id)
    heading = route_heading_continuity(route_edges, detector_edge_id)
    simplicity = route_simplicity(route_edges)
    score = (35.0 * 1.0) + (25.0 * proximity) + (15.0 * continuity) + (15.0 * heading) + (10.0 * simplicity)
    return score, continuity, heading, simplicity


def build_candidates(
    net,
    site: SiteInfo,
    min_detector_edge_length: float,
    min_endpoint_edge_length: float,
    detector_limit: int,
    max_distance: float,
) -> list[CandidateTriple]:
    ranked = []
    for detector_edge, detector_distance in candidate_detector_edges(
        net=net,
        site=site,
        min_edge_length=min_detector_edge_length,
        limit=detector_limit,
        max_distance=max_distance,
    ):
        lane = passenger_lane(detector_edge)
        if lane is None:
            continue

        upstream = collect_directional_edges(
            detector_edge,
            "upstream",
            min_edge_length=min_endpoint_edge_length,
            max_hops=3,
        )
        downstream = collect_directional_edges(
            detector_edge,
            "downstream",
            min_edge_length=min_endpoint_edge_length,
            max_hops=3,
        )
        if not upstream or not downstream:
            continue

        for source_edge, source_hops in upstream:
            for sink_edge, sink_hops in downstream:
                if source_edge.getID() == sink_edge.getID():
                    continue
                route = net.getShortestPath(source_edge, sink_edge, vClass="passenger")
                if route is None:
                    continue
                route_edges, route_cost = route
                if not route_edges:
                    continue
                route_ids = [edge.getID() for edge in route_edges]
                if detector_edge.getID() not in route_ids:
                    continue

                score, continuity, heading, simplicity = score_triple(
                    route_edges=route_edges,
                    detector_edge_id=detector_edge.getID(),
                    detector_distance_m=detector_distance,
                )

                ranked.append(
                    CandidateTriple(
                        source_edge=source_edge.getID(),
                        detector_edge=detector_edge.getID(),
                        sink_edge=sink_edge.getID(),
                        source_hops=source_hops,
                        sink_hops=sink_hops,
                        route_edges=route_ids,
                        route_cost=float(route_cost),
                        route_length_m=sum(edge.getLength() for edge in route_edges),
                        route_edge_count=len(route_edges),
                        detector_distance_m=float(detector_distance),
                        detector_lane=lane.getID(),
                        detector_pos=compute_detector_pos(lane.getLength()),
                        detector_name=edge_name(detector_edge),
                        source_name=edge_name(source_edge),
                        sink_name=edge_name(sink_edge),
                        street_continuity=continuity,
                        heading_continuity=heading,
                        simplicity=simplicity,
                        score=score,
                    )
                )

    ranked.sort(
        key=lambda candidate: (
            -candidate.score,
            candidate.detector_distance_m,
            candidate.route_edge_count,
            candidate.route_length_m,
        )
    )
    deduped = []
    seen = set()
    for candidate in ranked:
        key = (candidate.source_edge, candidate.detector_edge, candidate.sink_edge)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def ensure_net_link(site_dir: Path, net_path: Path) -> str:
    link_path = site_dir / net_path.name
    if link_path.exists() or link_path.is_symlink():
        if link_path.resolve() != net_path.resolve():
            raise RuntimeError(
                f"{link_path} already exists but does not point at {net_path}."
            )
        return net_path.name

    relative_target = os.path.relpath(net_path, start=site_dir)
    os.symlink(relative_target, link_path)
    return net_path.name


def write_site_assets(site_dir: Path, site: SiteInfo, net_file_name: str, selected: CandidateTriple) -> None:
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "sim.sumocfg").write_text(SIMCFG_TEMPLATE.format(net_file=net_file_name), encoding="utf-8")
    (site_dir / "detectors.add.xml").write_text(
        DETECTORS_TEMPLATE.format(
            site_id=site.site_id,
            score=selected.score,
            distance=selected.detector_distance_m,
            lane_id=selected.detector_lane,
            pos=selected.detector_pos,
        ),
        encoding="utf-8",
    )
    (site_dir / "miniTAZ.xml").write_text(
        TAZ_TEMPLATE.format(
            site_id=site.site_id,
            source_edge=selected.source_edge,
            detector_edge=selected.detector_edge,
            sink_edge=selected.sink_edge,
        ),
        encoding="utf-8",
    )
    if not (site_dir / "od_file.od").exists():
        (site_dir / "od_file.od").write_text(OD_TEMPLATE, encoding="utf-8")
    (site_dir / "README.md").write_text(
        README_TEMPLATE.format(
            site_id=site.site_id,
            description=site.description,
            region=site.region,
            lat=site.lat,
            lon=site.lon,
            net_file=net_file_name,
            source_edge=selected.source_edge,
            detector_lane=selected.detector_lane,
            sink_edge=selected.sink_edge,
            score=selected.score,
            distance=selected.detector_distance_m,
        ),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    site_dir = Path(args.site_dir).resolve()
    site_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = Path(args.site_metadata).resolve()
    net_path = Path(args.net_file).resolve()
    net = sumolib.net.readNet(str(net_path), withInternal=False)
    site = load_site_info(metadata_path=metadata_path, site_id=args.site_id, net_path=net_path)
    candidates = build_candidates(
        net=net,
        site=site,
        min_detector_edge_length=args.min_detector_edge_length,
        min_endpoint_edge_length=args.min_endpoint_edge_length,
        detector_limit=args.detector_edge_limit,
        max_distance=args.max_detector_distance,
    )

    report = {
        "site": asdict(site),
        "net_file": str(net_path),
        "candidate_count": len(candidates),
        "manual_review_threshold": args.manual_review_threshold,
        "top_candidates": [asdict(candidate) for candidate in candidates[: args.top_k]],
    }

    selected = candidates[0] if candidates else None
    if selected and selected.score >= args.manual_review_threshold:
        report["status"] = "candidate_selected"
        report["selected_candidate"] = asdict(selected)
        if args.write_assets:
            net_file_name = net_path.name
            if args.link_net:
                net_file_name = ensure_net_link(site_dir=site_dir, net_path=net_path)
            write_site_assets(site_dir=site_dir, site=site, net_file_name=net_file_name, selected=selected)
    else:
        report["status"] = "manual_review_required"
        report["selected_candidate"] = asdict(selected) if selected else None

    (site_dir / "corridor_proposal.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
