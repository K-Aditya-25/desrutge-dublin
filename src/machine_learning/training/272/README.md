# Dublin SUMO Scenario for Site 272

This folder contains the first-pass Dublin SUMO assets for SCATS site `272` generated from the reusable corridor proposer.

## Site

- `site_id`: 272
- `description`: COLLEGE GREEN / CHURCH LANE
- `region`: CCITY
- `lat`: 53.34435519
- `long`: -6.26085065

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `4476041#0`
- `detector lane`: `4476041#1_0`
- `sink edge`: `4476041#2`
- `proposal score`: `83.28`
- `detector distance to site marker`: `12.04` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/272 --run`
