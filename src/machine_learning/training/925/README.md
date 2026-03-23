# Dublin SUMO Scenario for Site 925

This folder contains the first-pass Dublin SUMO assets for SCATS site `925` generated from the reusable corridor proposer.

## Site

- `site_id`: 925
- `description`: PARNELL ST / DOMINIC ST
- `region`: CCITY
- `lat`: 53.35087364
- `long`: -6.264865487

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `928725821#2`
- `detector lane`: `928725821#3_0`
- `sink edge`: `1097499207`
- `proposal score`: `84.88`
- `detector distance to site marker`: `0.85` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/925 --run`
