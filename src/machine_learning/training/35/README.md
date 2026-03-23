# Dublin SUMO Scenario for Site 35

This folder contains the first-pass Dublin SUMO assets for SCATS site `35` generated from the reusable corridor proposer.

## Site

- `site_id`: 35
- `description`: NICHOLAS ST @ CHRISTCHURCH PL
- `region`: SCITY
- `lat`: 53.342866
- `long`: -6.271874

## Active SUMO Assets

- `net-file`: `osm_dublin_bigger.net.xml`
- `source edge`: `143866308#0`
- `detector lane`: `143866308#1_0`
- `sink edge`: `360313821`
- `proposal score`: `83.21`
- `detector distance to site marker`: `10.21` meters

## Notes

- This is a heuristic first-pass corridor mapping, not yet a hand-tuned `netedit` result.
- Candidate rankings and the full proposal report are recorded in `corridor_proposal.json`.
- The detector/source/sink assets were written only after the top-ranked candidate cleared the configured review threshold.

## Validation

- Full site validation on the VM:
  - `UV_CACHE_DIR=.uv-cache uv run python scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/35 --run`
