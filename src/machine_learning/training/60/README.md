# Dublin SUMO Scenario for Site 60

This folder contains the first-pass Dublin SUMO assets for SCATS site `60` generated from the reusable corridor proposer.

## Site

- `site_id`: 60
- `description`: DORSET ST @ GRANBY ROW & PED AT PARNELL SQ
- `region`: NCITY
- `lat`: 53.35423
- `long`: -6.266954

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `4395627#2`
- `detector lane`: `4395699#0_0`
- `sink edge`: `4395699#1`
- `proposal score`: `84.89`
- `detector distance to site marker`: `0.26` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/60 --run`
