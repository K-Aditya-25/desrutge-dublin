# Dublin SUMO Scenario for Site 665

This folder contains the first-pass Dublin SUMO assets for SCATS site `665` generated from the reusable corridor proposer.

## Site

- `site_id`: 665
- `description`: LORD EDWARD ST / FISHAMBLE ST (& LORD EDWARD ST @ COWS LANE)
- `region`: CCITY
- `lat`: 53.34360607
- `long`: -6.270067957

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `1254511880#1`
- `detector lane`: `5976028#2_0`
- `sink edge`: `5976028#3`
- `proposal score`: `80.10`
- `detector distance to site marker`: `8.03` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/665 --run`
