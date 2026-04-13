#!/usr/bin/env python3
"""Render a static Dublin Voronoi map on top of OpenStreetMap tiles."""

from __future__ import annotations

import argparse
import colorsys
import json
import math
import urllib.request
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont


TILE_SIZE = 256
OSM_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
LABEL_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LABEL_FONT_SIZE = 24


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render selected Dublin Voronoi cells on a static map.")
    parser.add_argument(
        "--geojson",
        default="./data/TrafficGeneration/dublin_march_2025/voronoi_site_cells.geojson",
        help="Voronoi GeoJSON input path.",
    )
    parser.add_argument(
        "--site-filter-json",
        required=True,
        help="Topology JSON path used to select the site subset and adjacency links.",
    )
    parser.add_argument(
        "--output-png",
        required=True,
        help="PNG output path.",
    )
    parser.add_argument(
        "--zoom",
        type=int,
        default=16,
        help="OSM tile zoom level.",
    )
    parser.add_argument(
        "--padding",
        type=float,
        default=0.15,
        help="Bounding-box padding as a fraction of width/height.",
    )
    parser.add_argument(
        "--show-adjacency",
        action="store_true",
        help="Draw dotted adjacency links between neighboring sites.",
    )
    parser.add_argument(
        "--show-site-labels",
        action="store_true",
        help="Draw site_id labels on top of the Voronoi zones.",
    )
    parser.add_argument(
        "--tile-cache-dir",
        default="./tmp/osm_tile_cache",
        help="Directory for caching downloaded OSM tiles.",
    )
    return parser.parse_args()


def color_for_site(site_id: str) -> tuple[int, int, int]:
    hash_value = 0
    for char in site_id:
        hash_value = ((hash_value << 5) - hash_value) + ord(char)
        hash_value &= 0xFFFFFFFF
    hue = abs(hash_value) % 360
    red, green, blue = colorsys.hls_to_rgb(hue / 360.0, 0.67, 0.55)
    return int(red * 255), int(green * 255), int(blue * 255)


def lonlat_to_world_pixels(lon: float, lat: float, zoom: int) -> tuple[float, float]:
    scale = TILE_SIZE * (2**zoom)
    x = (lon + 180.0) / 360.0 * scale
    lat_rad = math.radians(lat)
    y = (1.0 - math.log(math.tan(lat_rad) + (1.0 / math.cos(lat_rad))) / math.pi) / 2.0 * scale
    return x, y


def world_pixels_to_tile(px: float, py: float) -> tuple[int, int]:
    return int(px // TILE_SIZE), int(py // TILE_SIZE)


def filter_geojson(geojson: dict, allowed_sites: set[str]) -> list[dict]:
    return [feature for feature in geojson["features"] if str(feature["properties"]["site_id"]) in allowed_sites]


def compute_bounds(features: list[dict], padding_fraction: float) -> tuple[float, float, float, float]:
    min_lon = math.inf
    min_lat = math.inf
    max_lon = -math.inf
    max_lat = -math.inf
    for feature in features:
        for ring in feature["geometry"]["coordinates"]:
            for lon, lat in ring:
                min_lon = min(min_lon, lon)
                max_lon = max(max_lon, lon)
                min_lat = min(min_lat, lat)
                max_lat = max(max_lat, lat)

    lon_pad = (max_lon - min_lon) * padding_fraction
    lat_pad = (max_lat - min_lat) * padding_fraction
    return min_lon - lon_pad, min_lat - lat_pad, max_lon + lon_pad, max_lat + lat_pad


def fetch_tile(cache_dir: Path, zoom: int, tile_x: int, tile_y: int) -> Image.Image:
    tile_path = cache_dir / str(zoom) / str(tile_x) / f"{tile_y}.png"
    tile_path.parent.mkdir(parents=True, exist_ok=True)
    if not tile_path.exists():
        url = OSM_TILE_URL.format(z=zoom, x=tile_x, y=tile_y)
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "desrutge-dublin-voronoi-renderer/1.0 (research visualization)",
                "Accept": "image/png,image/*;q=0.9,*/*;q=0.8",
                "Referer": "https://www.openstreetmap.org/",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            tile_path.write_bytes(response.read())
    return Image.open(tile_path).convert("RGBA")


def build_basemap(bounds: tuple[float, float, float, float], zoom: int, cache_dir: Path) -> tuple[Image.Image, tuple[float, float]]:
    min_lon, min_lat, max_lon, max_lat = bounds
    min_px, max_py = lonlat_to_world_pixels(min_lon, min_lat, zoom)
    max_px, min_py = lonlat_to_world_pixels(max_lon, max_lat, zoom)

    min_tile_x, min_tile_y = world_pixels_to_tile(min_px, min_py)
    max_tile_x, max_tile_y = world_pixels_to_tile(max_px, max_py)

    canvas = Image.new(
        "RGBA",
        ((max_tile_x - min_tile_x + 1) * TILE_SIZE, (max_tile_y - min_tile_y + 1) * TILE_SIZE),
    )
    for tile_x in range(min_tile_x, max_tile_x + 1):
        for tile_y in range(min_tile_y, max_tile_y + 1):
            tile = fetch_tile(cache_dir, zoom, tile_x, tile_y)
            canvas.paste(tile, ((tile_x - min_tile_x) * TILE_SIZE, (tile_y - min_tile_y) * TILE_SIZE))

    crop_left = int(round(min_px - min_tile_x * TILE_SIZE))
    crop_top = int(round(min_py - min_tile_y * TILE_SIZE))
    crop_right = int(round(max_px - min_tile_x * TILE_SIZE))
    crop_bottom = int(round(max_py - min_tile_y * TILE_SIZE))
    return canvas.crop((crop_left, crop_top, crop_right, crop_bottom)), (min_px, min_py)


def lonlat_to_image_pixels(
    lon: float,
    lat: float,
    zoom: int,
    top_left_world_px: tuple[float, float],
) -> tuple[float, float]:
    world_x, world_y = lonlat_to_world_pixels(lon, lat, zoom)
    return world_x - top_left_world_px[0], world_y - top_left_world_px[1]


def draw_dashed_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    dash_length: int = 10,
    gap_length: int = 8,
    fill: tuple[int, int, int, int] = (30, 41, 59, 180),
    width: int = 3,
) -> None:
    start_x, start_y = start
    end_x, end_y = end
    delta_x = end_x - start_x
    delta_y = end_y - start_y
    distance = math.hypot(delta_x, delta_y)
    if distance == 0:
        return
    step_x = delta_x / distance
    step_y = delta_y / distance

    offset = 0.0
    while offset < distance:
        dash_end = min(offset + dash_length, distance)
        segment = (
            start_x + step_x * offset,
            start_y + step_y * offset,
            start_x + step_x * dash_end,
            start_y + step_y * dash_end,
        )
        draw.line(segment, fill=fill, width=width)
        offset += dash_length + gap_length


def main() -> None:
    args = parse_args()
    geojson = json.loads(Path(args.geojson).read_text(encoding="utf-8"))
    topology = json.loads(Path(args.site_filter_json).read_text(encoding="utf-8"))
    allowed_sites = {str(site_id) for site_id in topology.keys()}
    features = filter_geojson(geojson, allowed_sites)
    bounds = compute_bounds(features, args.padding)

    cache_dir = Path(args.tile_cache_dir).resolve()
    basemap, top_left_world_px = build_basemap(bounds, args.zoom, cache_dir)
    overlay = Image.new("RGBA", basemap.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    label_font = ImageFont.truetype(LABEL_FONT_PATH, LABEL_FONT_SIZE)

    site_points: dict[str, tuple[float, float]] = {}

    for feature in features:
        site_id = str(feature["properties"]["site_id"])
        outline = color_for_site(site_id)
        fill = (*outline, 80)
        for ring in feature["geometry"]["coordinates"]:
            pixels = [
                lonlat_to_image_pixels(lon, lat, args.zoom, top_left_world_px)
                for lon, lat in ring
            ]
            draw.polygon(pixels, fill=fill, outline=(*outline, 170))
            draw.line(pixels, fill=(*outline, 200), width=3)

        site_points[site_id] = lonlat_to_image_pixels(
            float(feature["properties"]["long"]),
            float(feature["properties"]["lat"]),
            args.zoom,
            top_left_world_px,
        )

    if args.show_adjacency:
        seen_edges: set[tuple[str, str]] = set()
        for site_id, node in topology.items():
            for neighbor in node.get("neighbors", []):
                neighbor_id = str(neighbor)
                if site_id not in site_points or neighbor_id not in site_points:
                    continue
                edge = tuple(sorted((str(site_id), neighbor_id)))
                if edge in seen_edges:
                    continue
                seen_edges.add(edge)
                draw_dashed_line(draw, site_points[edge[0]], site_points[edge[1]])

    for point_x, point_y in site_points.values():
        draw.ellipse((point_x - 7, point_y - 7, point_x + 7, point_y + 7), fill=(255, 255, 255, 255), outline=(17, 24, 39, 230), width=2)

    if args.show_site_labels:
        for site_id, (point_x, point_y) in site_points.items():
            label = str(site_id)
            bbox = draw.textbbox((0, 0), label, font=label_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            pad_x = 10
            pad_y = 7
            rect = (
                point_x - (text_width / 2) - pad_x,
                point_y - 34 - text_height - pad_y,
                point_x + (text_width / 2) + pad_x,
                point_y - 34 + pad_y,
            )
            draw.rectangle(rect, fill=(255, 255, 255, 235), outline=(0, 0, 0, 255), width=2)
            draw.text(
                (point_x - (text_width / 2), point_y - 34 - text_height),
                label,
                fill=(0, 0, 0, 255),
                font=label_font,
            )

    rendered = Image.alpha_composite(basemap, overlay).convert("RGB")
    output_path = Path(args.output_png).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rendered.save(output_path, format="PNG")
    print(f"Wrote static map to {output_path}")


if __name__ == "__main__":
    main()
