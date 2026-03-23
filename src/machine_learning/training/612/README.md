# Dublin SUMO Scenario for Site 612

This folder contains the first-pass Dublin SUMO assets for SCATS site `612` generated from the reusable corridor proposer.

## Site

- `site_id`: 612
- `description`: ABBEY STREET MIDDLE @ LIFFEY ST (LUAS)
- `region`: CCITY
- `lat`: 53.34793766
- `long`: -6.263643766

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `39994843#1`
- `detector lane`: `14401069#0_0`
- `sink edge`: `14401069#1`
- `proposal score`: `83.06`
- `detector distance to site marker`: `12.48` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/612 --run`
