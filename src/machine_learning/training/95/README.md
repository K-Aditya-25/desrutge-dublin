# Dublin SUMO Scenario for Site 95

This folder scaffolds the SUMO inputs expected by the DesRUTGe traffic pipeline for Dublin SCATS site `95`.

## Site

- `site_id`: 95
- `description`: JERVIS ST @ MARY ST
- `region`: CCITY
- `lat`: 53.348808
- `long`: -6.26667

## Required files

The site now uses real local Dublin SUMO assets on the larger cropped net:

- `osm_dublin_bigger.net.xml`
- `miniTAZ.xml`
- `detectors.add.xml`
- `sim.sumocfg`

## Recommended local workflow

1. Download an OpenStreetMap extract that covers the site and nearby approaches.
2. Convert it into a SUMO net with `netconvert`.
3. Open the net in `netedit` and identify the approaches corresponding to this SCATS site.
4. Create `detectors.add.xml` with induction loops on those lanes.
5. Create `miniTAZ.xml` with a single site-centric zone and candidate source/sink edges.
6. Validate the site with:
   - `od2trips -n miniTAZ.xml -d od_file.od -o trips.xml`
   - `duarouter -n osm_dublin_bigger.net.xml -t trips_via.xml -o routes.rou.xml --additional-files miniTAZ.xml --ignore-errors --no-warnings`
   - `sumo -c sim.sumocfg --no-warnings`

## Larger Dublin Context Workflow

If the small `.osm` extract does not provide enough road context around the site, build a larger cropped Dublin net directly from the Geofabrik `.osm.pbf`:

```bash
python3 ./scripts/build_dublin_site_net.py \
  --osm-file "./data/DublinData/Ireland Northern Ireland.osm.pbf" \
  --site-dir "./src/machine_learning/training/95" \
  --output-net "osm_dublin_bigger.net.xml" \
  --dublin-boundary \
  --lefthand
```

Then inspect it with:

```bash
netedit "./src/machine_learning/training/95/osm_dublin_bigger.net.xml"
```

## Notes

- The current repo expects this directory to be named exactly after the site id.
- Site `95` currently uses:
  - source edge `33920769#2`
  - detector lane `33920769#3_0`
  - sink edge `33920769#4`
- Local geometry validation:
  - `python3 ./scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/95 --run`
- Local 24-hour evaluation:
  - `python3 ./scripts/evaluate_one_site_sumo.py --site-dir ./src/machine_learning/training/95 --site-id 95 --mode daily-profile`
- Local routing sanity check for one hour:
  - `python3 ./scripts/evaluate_one_site_sumo.py --site-dir ./src/machine_learning/training/95 --site-id 95 --mode hourly-debug --hour 8`
- PPO execution on this MacBook is still blocked by:
  - `OMP: Error #179: Can't open SHM2`
