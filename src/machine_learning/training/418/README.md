# Dublin SUMO Scenario for Site 418

This folder contains the first-pass Dublin SUMO assets for SCATS site `418` generated from the reusable corridor proposer.

## Site

- `site_id`: 418
- `description`: CAPEL ST @ ABBEY ST (LUAS)
- `region`: CCITY
- `lat`: 53.347297
- `long`: -6.268342

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `1062391649`
- `detector lane`: `23086918_0`
- `sink edge`: `1062391648`
- `proposal score`: `84.52`
- `detector distance to site marker`: `1.68` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/418 --run`
