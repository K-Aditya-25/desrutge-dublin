# Dublin SUMO Scenario for Site 419

This folder contains the first-pass Dublin SUMO assets for SCATS site `419` generated from the reusable corridor proposer.

## Site

- `site_id`: 419
- `description`: PARNELL ST / JERVIS ST / CHAPEL LANE
- `region`: CCITY
- `lat`: 53.3501487
- `long`: -6.2668778

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `33920769#5`
- `detector lane`: `1315558444#0_0`
- `sink edge`: `1315558444#1`
- `proposal score`: `82.07`
- `detector distance to site marker`: `23.41` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/419 --run`
