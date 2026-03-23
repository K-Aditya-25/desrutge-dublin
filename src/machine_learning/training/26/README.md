# Dublin SUMO Scenario for Site 26

This folder contains the first-pass Dublin SUMO assets for SCATS site `26` generated from the reusable corridor proposer.

## Site

- `site_id`: 26
- `description`: CAPEL ST BRIDGE
- `region`: CCITY
- `lat`: 53.345694
- `long`: -6.267771

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `31028273`
- `detector lane`: `375772040_0`
- `sink edge`: `1179644970#0`
- `proposal score`: `84.86`
- `detector distance to site marker`: `1.14` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/26 --run`
