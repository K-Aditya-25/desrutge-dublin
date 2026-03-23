# Dublin SUMO Scenario for Site 936

This folder contains the first-pass Dublin SUMO assets for SCATS site `936` generated from the reusable corridor proposer.

## Site

- `site_id`: 936
- `description`: BACHELORS WALK BUS GATE
- `region`: CCITY
- `lat`: 53.347106
- `long`: -6.261071

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `1064203149#1`
- `detector lane`: `25094727_0`
- `sink edge`: `1008768007`
- `proposal score`: `84.20`
- `detector distance to site marker`: `4.24` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/936 --run`
