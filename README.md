# DesRUTGe: Realistic Urban Traffic Generator using Decentralized Federated Learning for the SUMO simulator

This repository adapts DesRUTGe toward Dublin SCATS traffic data while keeping the repo's SUMO + PPO + federated/decentralized structure.

The current repo state is centered on:

- Dublin SCATS preprocessing into site-level hourly profiles
- per-site SUMO scenario authoring under `src/machine_learning/training/<site_id>/`
- Dublin Voronoi-derived topology generation
- bounded SUMO-backed decentralized smoke runs on a curated 18-site cloud subset

## Project Structure

- `config/`: topology and simulation configuration JSON files
- `data/`: raw Dublin inputs and processed traffic artifacts
- `docs/`: Dublin workflow and execution notes
- `scripts/`: preprocessing, SUMO-site authoring, topology, validation, and evaluation helpers
- `src/`: simulation source code
  - `src/entities/`: centralized/decentralized node roles
  - `src/machine_learning/dataset/`: dataset loaders and traffic-profile preparation
  - `src/machine_learning/training/`: PPO traffic environment, SUMO runtime, and per-site SUMO folders
  - `src/simulator/`: orchestration of centralized and decentralized simulation runs
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

Current Python dependencies are defined in `pyproject.toml`. Key packages include:

- `torch==2.0.1`
- `torchvision==0.15.2`
- `stable-baselines3==2.2.1`
- `gymnasium==0.29.1`
- `numpy==1.24.1`
- `pandas==1.5.3`
- `scikit-learn==1.4.1.post1`
- `scipy==1.11.3`
- `shapely`
- `osmium`
- `matplotlib==3.7.1`
- `seaborn==0.13.0`
- `lxml`

## Installation

Clone the repository:

```bash
git clone https://gitlab.com/compromise3/desrutge.git
cd desrutge
```

Using `uv` is the current preferred path:

```bash
uv sync
```

If you are using plain `pip`, install from the repo metadata or `requirements.txt`:

```bash
pip install -e .
```

or:

```bash
pip install -r requirements.txt
```

## Current Repo Behavior

Important current behavior for the Dublin traffic path:

- `Traffic_Generator` now defaults to the SUMO-backed path via `--trafficSimulationMode sumo`
- surrogate mode remains available as `--trafficSimulationMode test`
- the PPO environment uses Gymnasium
- the traffic path is a deep reinforcement learning setup:
  - it uses `stable-baselines3` PPO with `MlpPolicy`
  - `MlpPolicy` is a neural-network policy/value model supplied by SB3
  - the neural-network architecture is library-provided rather than manually defined in this repo
- traffic profiles are bound by `site_id`, not CSV position
- per-node model export is opt-in via `--saveNodeModels`

## Usage

### Decentralized Dublin smoke run

The currently representative bounded 18-site decentralized smoke command is:

```bash
python3 ./src/main_sim_decentralized.py \
  -r 1 \
  -t ./config/dublin_voronoi_first_cloud_18.json \
  -a Mean \
  -db Traffic_Generator \
  --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ \
  --trafficSimulationMode sumo \
  --trafficTotalTimesteps 1 \
  --trafficEpisodeMaxSteps 1 \
  --trafficTestEpisodes 1 \
  -o ./output/decentralized_sim/dublin_first_cloud_18_mean_r1_smoke.json
```

### Centralized example

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

### Key CLI parameters

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

## Dublin SCATS Preprocessing

The public repo does not include the original Barcelona traffic counts, and the root `data/TrafficGeneration/detector_data.csv` file is intentionally redacted for public release. For the Dublin path, use the processed Dublin dataset or regenerate it from raw Dublin inputs.

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

The repo currently includes:

- `config/dublin_single_site_95.json`
- `config/dublin_voronoi_smoke_5.json`
- `config/dublin_voronoi_topology.json`
- `config/dublin_voronoi_first_cloud_18.json`

The full Voronoi topology has `642` topology-ready sites.
The current practical cloud target is the connected 18-site subset in `config/dublin_voronoi_first_cloud_18.json`.

## SUMO Site Workflow

The first local proof site remains site `95`:

- folder: `src/machine_learning/training/95/`
- current larger-net mapping:
  - source edge `33920769#2`
  - detector lane `33920769#3_0`
  - sink edge `33920769#4`

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

## Current Status

At the current repo snapshot:

- Dublin preprocessing is implemented
- Dublin Voronoi topology generation is implemented
- site `95` is locally SUMO-runnable on the larger Dublin net
- all `18/18` sites in the first-cloud subset have first-pass SUMO folders
- bounded decentralized SUMO smoke execution for that subset has been verified
- full-budget runs are still expensive and should be ramped up gradually

## Reference to the Paper

This code was originally presented in the following publication:

> **Alberto Bazán-Guillén, Carlos Beis-Penedo, Diego Cajaraville-Aboy, Pablo Barbecho-Bautista, Rebeca P. Díaz-Redondo, Luis J. de la Cruz Llopis, Ana Fernández-Vilas, Mónica Aguilar Igartua, Manuel Fernández-Veiga**, *"Realistic Urban Traffic Generator using Decentralized Federated Learning for the SUMO simulator"*, IEEE Open Journal of the Communications Society, ISSN: 2644-125X, 8th August 2025, **DOI:** [10.1109/OJCOMS.2025.3597019](https://ieeexplore.ieee.org/document/11121363).

If you use or modify this code in your research, please cite the paper.

## License

This project is licensed under the GNU GPLv3 License. See `LICENSE`.
