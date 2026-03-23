# Dublin SUMO Scenario for Site 202

This folder contains the first-pass Dublin SUMO assets for SCATS site `202` generated from the reusable corridor proposer.

## Site

- `site_id`: 202
- `description`: PARNELL ST @ PARNELL SQ & PED AT DOMINICK ST
- `region`: CCITY
- `lat`: 53.35182721
- `long`: -6.262915529

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `1390518836#1`
- `detector lane`: `1170418365_0`
- `sink edge`: `1390518837`
- `proposal score`: `84.13`
- `detector distance to site marker`: `3.46` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/202 --run`
