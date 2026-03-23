# Dublin SUMO Scenario for Site 50

This folder contains the first-pass Dublin SUMO assets for SCATS site `50` generated from the reusable corridor proposer.

## Site

- `site_id`: 50
- `description`: DAME ST @ TRINITY ST
- `region`: CCITY
- `lat`: 53.34424291
- `long`: -6.262293315

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `52879957#1`
- `detector lane`: `-304634278#1_0`
- `sink edge`: `-304634278#0`
- `proposal score`: `83.82`
- `detector distance to site marker`: `7.92` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/50 --run`
