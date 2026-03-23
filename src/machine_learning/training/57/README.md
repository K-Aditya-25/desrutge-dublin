# Dublin SUMO Scenario for Site 57

This folder contains the first-pass Dublin SUMO assets for SCATS site `57` generated from the reusable corridor proposer.

## Site

- `site_id`: 57
- `description`: DORSET ST @ ECCLES ST
- `region`: NCITY
- `lat`: 53.357511
- `long`: -6.263842

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `83806428#2`
- `detector lane`: `-111286353#7_0`
- `sink edge`: `-111286353#6`
- `proposal score`: `82.31`
- `detector distance to site marker`: `3.58` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/57 --run`
