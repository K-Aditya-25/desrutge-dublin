# Dublin SUMO Scenario for Site 711

This folder contains the first-pass Dublin SUMO assets for SCATS site `711` generated from the reusable corridor proposer.

## Site

- `site_id`: 711
- `description`: CAPEL ST @ STRAND ST (LUAS)
- `region`: CCITY
- `lat`: 53.34648366
- `long`: -6.268027771

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `1478689539#1`
- `detector lane`: `1478689540_0`
- `sink edge`: `1132213866`
- `proposal score`: `84.73`
- `detector distance to site marker`: `0.43` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/711 --run`
