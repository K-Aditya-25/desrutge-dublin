# Dublin SUMO Scenario for Site 140

This folder contains the first-pass Dublin SUMO assets for SCATS site `140` generated from the reusable corridor proposer.

## Site

- `site_id`: 140
- `description`: PARNELL SQ @ NORTH FREDERICK ST
- `region`: NCITY
- `lat`: 53.35442851
- `long`: -6.263430138

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `-1297449764`
- `detector lane`: `-37692391_0`
- `sink edge`: `-1297451097`
- `proposal score`: `80.90`
- `detector distance to site marker`: `31.59` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/140 --run`
