#!/usr/bin/env python3
"""Render Dublin Voronoi GeoJSON as a lightweight Leaflet HTML map."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    crossorigin=""
  />
  <style>
    html, body, #map {{
      height: 100%;
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .panel {{
      position: absolute;
      top: 12px;
      right: 12px;
      z-index: 1000;
      background: rgba(255, 255, 255, 0.94);
      padding: 10px 12px;
      border-radius: 10px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
      max-width: 320px;
      line-height: 1.35;
    }}
    .panel h1 {{
      font-size: 16px;
      margin: 0 0 6px 0;
    }}
    .panel p {{
      font-size: 12px;
      margin: 0 0 6px 0;
    }}
    .leaflet-popup-content {{
      font-size: 12px;
      line-height: 1.35;
    }}
    .legend-swatch {{
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 2px;
      margin-right: 6px;
      vertical-align: middle;
    }}
  </style>
</head>
<body>
  <div id="map"></div>
  <div class="panel">
    <h1>{title}</h1>
    <p>{summary}</p>
    <p><span class="legend-swatch" style="background:{sample_color};"></span>Voronoi cells</p>
    <p><span class="legend-swatch" style="background:#111827;"></span>Subset adjacency links</p>
    <p><strong>Tip:</strong> click a cell or marker to inspect the site id and coordinates.</p>
  </div>
  <script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
    crossorigin=""
  ></script>
  <script>
    const voronoiData = {geojson};
    const adjacencyData = {adjacency_json};
    const map = L.map('map', {{ zoomSnap: 0.25 }});

    const tiles = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }}).addTo(map);

    function colorForSite(siteId) {{
      let hash = 0;
      for (let i = 0; i < siteId.length; i += 1) {{
        hash = ((hash << 5) - hash) + siteId.charCodeAt(i);
        hash |= 0;
      }}
      const hue = Math.abs(hash) % 360;
      return `hsl(${{hue}}, 65%, 55%)`;
    }}

    function popupHtml(properties) {{
      const parts = [
        `<strong>Site ${{properties.site_id}}</strong>`,
        `Lat: ${{Number(properties.lat).toFixed(6)}}`,
        `Long: ${{Number(properties.long).toFixed(6)}}`
      ];
      if (properties.description) parts.push(`Description: ${{properties.description}}`);
      if (properties.region) parts.push(`Region: ${{properties.region}}`);
      if (properties.quality_flag) parts.push(`Quality: ${{properties.quality_flag}}`);
      return parts.join('<br/>');
    }}

    const cells = L.geoJSON(voronoiData, {{
      style: feature => {{
        const color = colorForSite(String(feature.properties.site_id));
        return {{
          color,
          weight: 1.1,
          opacity: 0.9,
          fillColor: color,
          fillOpacity: 0.28
        }};
      }},
      onEachFeature: (feature, layer) => {{
        layer.bindPopup(popupHtml(feature.properties));
      }}
    }}).addTo(map);

    const markers = L.layerGroup(
      voronoiData.features.map(feature => {{
        const lat = feature.properties.lat;
        const lng = feature.properties.long;
        return L.circleMarker([lat, lng], {{
          radius: 3.5,
          color: '#1f2937',
          weight: 1,
          fillColor: '#ffffff',
          fillOpacity: 0.95
        }}).bindPopup(popupHtml(feature.properties));
      }})
    ).addTo(map);

    const adjacencyLines = adjacencyData.edges.length
      ? L.layerGroup(
          adjacencyData.edges.map(edge => {{
            const from = adjacencyData.sites[String(edge[0])];
            const to = adjacencyData.sites[String(edge[1])];
            return L.polyline(
              [
                [from.lat, from.long],
                [to.lat, to.long]
              ],
              {{
                color: '#111827',
                weight: 2,
                opacity: 0.7,
                dashArray: '6 6'
              }}
            ).bindPopup(
              `<strong>Adjacency</strong><br/>Site ${{edge[0]}} <-> Site ${{edge[1]}}`
            );
          }})
        ).addTo(map)
      : null;

    const bounds = cells.getBounds();
    map.fitBounds(bounds.pad(0.02));
    const overlays = {{
      'Voronoi cells': cells,
      'Site markers': markers
    }};
    if (adjacencyLines) {{
      overlays['Adjacency links'] = adjacencyLines;
    }}
    L.control.layers(null, overlays, {{ collapsed: false }}).addTo(map);
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Dublin Voronoi zones to an HTML map.")
    parser.add_argument(
        "--geojson",
        default="./data/TrafficGeneration/dublin_march_2025/voronoi_site_cells.geojson",
        help="Voronoi GeoJSON input path.",
    )
    parser.add_argument(
        "--output-html",
        default="./data/TrafficGeneration/dublin_march_2025/voronoi_site_cells_map.html",
        help="HTML output path.",
    )
    parser.add_argument(
        "--site-filter-json",
        default=None,
        help="Optional topology JSON path. If provided, only sites present in that topology are rendered.",
    )
    parser.add_argument(
        "--title",
        default="Dublin Voronoi Zoning",
        help="Map title.",
    )
    return parser.parse_args()


def filter_features(geojson: dict, allowed_sites: set[str]) -> dict:
    filtered = [feature for feature in geojson["features"] if str(feature["properties"]["site_id"]) in allowed_sites]
    geojson = dict(geojson)
    geojson["features"] = filtered
    geojson["metadata"] = dict(geojson.get("metadata", {}))
    geojson["metadata"]["site_count"] = len(filtered)
    return geojson


def build_adjacency_overlay(geojson: dict, topology: dict[str, dict[str, object]] | None) -> dict:
    if not topology:
        return {"sites": {}, "edges": []}

    sites = {}
    for feature in geojson.get("features", []):
        properties = feature.get("properties", {})
        site_id = str(properties.get("site_id"))
        sites[site_id] = {
            "lat": properties.get("lat"),
            "long": properties.get("long"),
        }

    edges = []
    seen = set()
    for site_id, node in topology.items():
        for neighbor in node.get("neighbors", []):
            neighbor_id = str(neighbor)
            if site_id not in sites or neighbor_id not in sites:
                continue
            edge = tuple(sorted((site_id, neighbor_id), key=lambda value: int(value) if value.isdigit() else value))
            if edge in seen:
                continue
            seen.add(edge)
            edges.append([int(edge[0]) if edge[0].isdigit() else edge[0], int(edge[1]) if edge[1].isdigit() else edge[1]])

    return {"sites": sites, "edges": edges}


def main() -> None:
    args = parse_args()
    geojson_path = Path(args.geojson).resolve()
    output_path = Path(args.output_html).resolve()

    geojson = json.loads(geojson_path.read_text(encoding="utf-8"))
    topology = None
    if args.site_filter_json:
        topology = json.loads(Path(args.site_filter_json).resolve().read_text(encoding="utf-8"))
        allowed_sites = {str(site_id) for site_id in topology.keys()}
        geojson = filter_features(geojson, allowed_sites)

    site_count = len(geojson["features"])
    adjacency_overlay = build_adjacency_overlay(geojson, topology)
    edge_count = len(adjacency_overlay["edges"])
    sample_site = str(geojson["features"][0]["properties"]["site_id"]) if geojson["features"] else "0"
    sample_color = f"hsl({abs(hash(sample_site)) % 360}, 65%, 55%)"
    if edge_count:
        summary = f"Rendered {site_count} Voronoi zones and {edge_count} adjacency links from the selected Dublin subset."
    else:
        summary = f"Rendered {site_count} Voronoi zones from the Dublin topology-ready site set."
    html = HTML_TEMPLATE.format(
        title=args.title,
        summary=summary,
        sample_color=sample_color,
        geojson=json.dumps(geojson),
        adjacency_json=json.dumps(adjacency_overlay),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Wrote Voronoi map HTML to {output_path}")


if __name__ == "__main__":
    main()
