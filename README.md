# DesRUTGe Dublin

This repository adapts DesRUTGe toward Dublin SCATS traffic data while keeping the original SUMO, PPO, and decentralized federated-learning structure. The current codebase is centered on building per-site Dublin SUMO scenarios, running centralized or decentralized traffic calibration experiments, and generating figures and helper artifacts for the reduced Dublin subsets used in the repo.

## What Is In The Repo

- Dublin SCATS preprocessing into site-level hourly traffic profiles
- Per-site SUMO scenario folders under `src/machine_learning/training/<site_id>/`
- Dublin topology configs for single-site, reduced-subset, centralized-star, and wider Voronoi-derived runs
- A paper-faithful hourly PPO traffic contract that assembles full 24-hour profiles sequentially
- Helpers for validation, routeSampler baselines, topology derivation, and paper-style visualization outputs

## Project Structure

- `config/`: topology and simulation configuration JSON files
- `data/`: raw Dublin inputs and processed traffic artifacts
- `docs/`: workflow notes, execution notes, and generated paper-facing figures
- `scripts/`: preprocessing, topology, validation, evaluation, and plotting helpers
- `src/`: simulation source code
- `src/entities/`: centralized and decentralized node roles
- `src/machine_learning/dataset/`: traffic-profile loading and preparation
- `src/machine_learning/training/`: PPO traffic environment, SUMO runtime, and per-site SUMO folders
- `src/simulator/`: centralized and decentralized orchestration
- `src/main_sim_decentralized.py`: decentralized entrypoint
- `src/main_sim_centralized.py`: centralized entrypoint

## Requirements

- Python `>=3.10,<3.11`
- SUMO tooling available on the machine:
- `sumo`
- `od2trips`
- `duarouter`
- `netconvert`
- `netedit`

Dependencies are defined in [pyproject.toml](/home/adityakharbanda/desrutge-dublin/pyproject.toml). The main runtime stack includes `torch`, `stable-baselines3`, `gymnasium`, `numpy`, `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `shapely`, `osmium`, and `lxml`.

## Installation

Clone the repository:

```bash
git clone https://gitlab.com/compromise3/desrutge.git
cd desrutge
```

Using `uv` is the preferred path:

```bash
uv sync
```

If you are using plain `pip`:

```bash
pip install -e .
```

or:

```bash
pip install -r requirements.txt
```

## Simulation Behavior

Important repo behavior for the Dublin traffic path:

- `Traffic_Generator` uses the SUMO-backed path with `--trafficSimulationMode sumo`
- surrogate mode remains available as `--trafficSimulationMode test`
- the PPO environment uses Gymnasium
- the trainer uses `stable-baselines3` PPO with `MlpPolicy`
- one PPO environment step calibrates one hour and executes SUMO once
- full daily `h00..h23` profiles are assembled by chaining 24 hourly calibrations with residual carry-forward
- run outputs contain full 24-hour simulated profiles and per-profile metrics
- traffic profiles are keyed by `site_id`, not CSV position
- per-node model export is opt-in via `--saveNodeModels`

## Usage

### Decentralized Dublin 8-site smoke run

```bash
UV_CACHE_DIR=.uv-cache uv run --no-sync python ./src/main_sim_decentralized.py \
  -r 1 \
  -t ./config/dublin_voronoi_fast_8.json \
  -a Mean \
  -db Traffic_Generator \
  --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ \
  --trafficSimulationMode sumo \
  --trafficTotalTimesteps 1 \
  --trafficEpisodeMaxSteps 1 \
  --trafficTestEpisodes 1 \
  -o ./output/decentralized_sim/dublin_fast_8_hourly_sumo_r1_smoke.json
```

### Decentralized Dublin 18-site reference smoke

```bash
UV_CACHE_DIR=.uv-cache uv run --no-sync python ./src/main_sim_decentralized.py \
  -r 1 \
  -t ./config/dublin_voronoi_first_cloud_18.json \
  -a Mean \
  -db Traffic_Generator \
  --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ \
  --trafficSimulationMode sumo \
  --trafficTotalTimesteps 1 \
  --trafficEpisodeMaxSteps 1 \
  --trafficTestEpisodes 1 \
  -o ./output/decentralized_sim/dublin_first_cloud_18_hourly_sumo_r1_smoke.json
```

### Centralized Dublin example

```bash
python3 ./src/main_sim_centralized.py \
  -r 1 \
  -s 0 \
  -t ./config/centralized.json \
  -a Mean \
  -db Traffic_Generator \
  --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ \
  --trafficSimulationMode sumo \
  -o ./output/centralized_sim/centralized_mean.json
```

### Useful CLI parameters

- `-r`: communication rounds
- `-t`: topology JSON
- `-a`: aggregation algorithm
- `-db`: dataset
- `--trafficDataPath`: directory containing `detector_data.csv`
- `--trafficSimulationMode`: `sumo` or `test`
- `--trafficTotalTimesteps`: per-node PPO timesteps
- `--trafficEpisodeMaxSteps`: max environment steps per episode
- `--trafficTestEpisodes`: evaluation episodes per node after each round
- `--saveNodeModels`: export per-node trained models after the run
- `-o`: output JSON path

## Dublin Data Preprocessing

The public repo does not include the original Barcelona traffic counts, and the root `data/TrafficGeneration/detector_data.csv` file is intentionally redacted. For the Dublin path, use the processed Dublin dataset or regenerate it from raw Dublin inputs.

To preprocess Dublin SCATS hourly counts into the repo-facing format:

```bash
python3 ./scripts/preprocess_dublin_scats.py \
  --hourly-data ./data/DublinData/SCATSMarch2025.csv \
  --site-metadata "./data/DublinData/DCC Traffic Signals Nov 30 2022 (1).csv" \
  --dayfirst \
  --mode paper-faithful \
  --output-dir ./data/TrafficGeneration/dublin_march_2025
```

This produces artifacts such as:

- `detector_data.csv`
- `site_metadata.csv`
- `site_hourly_targets_long.csv`
- `site_date_hour_totals.csv`
- `preprocessing_summary.json`

## Dublin Topology Artifacts

The repo includes these Dublin topology configs:

- `config/dublin_single_site_95.json`
- `config/dublin_voronoi_smoke_5.json`
- `config/dublin_voronoi_fast_8.json`
- `config/dublin_centralized_fast_8_server_95.json`
- `config/dublin_voronoi_fast_8_pattern_affinity.json`
- `config/dublin_voronoi_fast_8_volume_affinity.json`
- `config/dublin_voronoi_topology.json`
- `config/dublin_voronoi_first_cloud_18.json`

In practice:

- `config/dublin_voronoi_fast_8.json` is the main reduced connected subset for fast decentralized runs
- `config/dublin_centralized_fast_8_server_95.json` is the server-95 star topology for centralized comparisons
- `config/dublin_voronoi_fast_8_pattern_affinity.json` and `config/dublin_voronoi_fast_8_volume_affinity.json` are affinity-derived alternatives for the same 8-site subset
- `config/dublin_voronoi_first_cloud_18.json` is the wider connected reference subset
- `config/dublin_voronoi_topology.json` is the larger topology-ready Dublin site graph

## SUMO Site Workflow

The per-site SUMO scenarios live under `src/machine_learning/training/`. Site `95` remains a useful local proof site for one-site validation and inspection.

Useful commands:

```bash
python3 ./scripts/validate_sumo_site.py --site-dir ./src/machine_learning/training/95 --run
```

```bash
python3 ./scripts/evaluate_one_site_sumo.py --site-dir ./src/machine_learning/training/95 --site-id 95 --mode daily-profile
```

```bash
python3 ./scripts/validate_dublin_framework.py --topology ./config/dublin_voronoi_smoke_5.json --traffic-simulation-mode test
```

## Analysis And Figure Helpers

The repo also includes Dublin-specific helpers for experiment support and paper-style outputs, including:

- `scripts/evaluate_routesampler_baseline.py`
- `scripts/build_dublin_affinity_topology.py`
- `scripts/render_dublin_affinity_dendrogram.py`
- `scripts/render_dublin_8site_round_scaling.py`
- `scripts/render_dublin_paper_visualizations.py`
- `scripts/render_dublin_voronoi_static_map.py`
- `scripts/render_site95_anchor_bar_chart.py`
- `scripts/render_site95_anchor_story.py`

Experiment notes and run logs are tracked in:

- `8siteExperiments.md`
- `8siteCentralizedExperiments.md`
- `18siteExperiments.md`
