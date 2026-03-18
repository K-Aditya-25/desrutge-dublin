#!/usr/bin/env python3
"""Build a SUMO network for one Dublin site from an OSM extract or PBF."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

DUBLIN_GEO_BOUNDARY = "-6.31,53.32,-6.18,53.44"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a SUMO net for a Dublin site folder from an OSM extract or Geofabrik PBF."
    )
    parser.add_argument("--osm-file", required=True, help="Path to the source .osm or .osm.pbf file.")
    parser.add_argument("--site-dir", required=True, help="Path to the site folder under src/machine_learning/training.")
    parser.add_argument(
        "--output-net",
        default="osm.net.xml",
        help="Output SUMO net filename inside the site directory.",
    )
    parser.add_argument(
        "--lefthand",
        action="store_true",
        help="Pass --lefthand to netconvert if the road network requires it.",
    )
    parser.add_argument(
        "--keep-ptstops",
        action="store_true",
        help="Keep public transport stops in the netconvert import.",
    )
    parser.add_argument(
        "--geo-boundary",
        help=(
            "Optional geographic boundary passed to netconvert as "
            "'west,south,east,north' via --keep-edges.in-geo-boundary."
        ),
    )
    parser.add_argument(
        "--dublin-boundary",
        action="store_true",
        help=f"Use the default Dublin crop boundary {DUBLIN_GEO_BOUNDARY}.",
    )
    return parser.parse_args()


def parse_boundary(boundary: str) -> tuple[str, str, str, str]:
    parts = [part.strip() for part in boundary.split(",")]
    if len(parts) != 4:
        raise ValueError(
            "Geo boundary must be provided as 'west,south,east,north'. "
            f"Received {boundary!r}."
        )
    return tuple(parts)


def maybe_convert_pbf_to_osm(osm_file: Path, geo_boundary: str | None) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if osm_file.suffix.lower() != ".pbf":
        return osm_file, None

    if geo_boundary is None:
        raise RuntimeError(
            "Refusing to convert a full-country .osm.pbf without a crop boundary. "
            "Pass --geo-boundary or --dublin-boundary."
        )

    try:
        import osmium
    except ImportError as exc:
        raise RuntimeError(
            "This netconvert build cannot read .osm.pbf directly here, and pyosmium is not installed. "
            "Install the Python 'osmium' package or convert the PBF to .osm first."
        ) from exc

    west, south, east, north = map(float, parse_boundary(geo_boundary))
    temp_dir = tempfile.TemporaryDirectory(prefix="dublin_pbf_")
    converted_osm = Path(temp_dir.name) / f"{osm_file.stem}.osm"
    selected_node_ids: set[int] = set()

    def in_boundary(lat: float, lon: float) -> bool:
        return south <= lat <= north and west <= lon <= east

    class BoundaryExtractor(osmium.SimpleHandler):
        def __init__(self, writer):
            super().__init__()
            self.writer = writer

        def node(self, node):
            if in_boundary(node.location.lat, node.location.lon):
                selected_node_ids.add(node.id)
                self.writer.add_node(node)

        def way(self, way):
            keep_way = False
            for way_node in way.nodes:
                if in_boundary(way_node.location.lat, way_node.location.lon):
                    keep_way = True
                    break

            if keep_way:
                self.writer.add_way(way)

    with osmium.BackReferenceWriter(
        str(converted_osm),
        str(osm_file),
        overwrite=True,
        remove_tags=False,
        relation_depth=0,
    ) as writer:
        BoundaryExtractor(writer).apply_file(str(osm_file), locations=True)

    return converted_osm, temp_dir


def main() -> None:
    args = parse_args()
    if shutil.which("netconvert") is None:
        raise RuntimeError("netconvert is not installed or not on PATH.")

    osm_file = Path(args.osm_file).resolve()
    site_dir = Path(args.site_dir).resolve()
    site_dir.mkdir(parents=True, exist_ok=True)
    output_net = site_dir / args.output_net

    geo_boundary = args.geo_boundary
    if args.dublin_boundary:
        geo_boundary = DUBLIN_GEO_BOUNDARY

    source_for_netconvert, temp_dir = maybe_convert_pbf_to_osm(osm_file, geo_boundary)

    command = ["netconvert", "--osm-files", str(source_for_netconvert), "-o", str(output_net)]
    if geo_boundary and source_for_netconvert == osm_file:
        command.extend(["--keep-edges.in-geo-boundary", geo_boundary])
    if args.lefthand:
        command.append("--lefthand")
    if args.keep_ptstops:
        command.extend(["--ptstop-output", str(site_dir / "ptstops.add.xml")])
    try:
        subprocess.run(command, check=True)
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()
    print(output_net)


if __name__ == "__main__":
    main()
