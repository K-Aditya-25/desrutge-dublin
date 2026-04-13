# 8-Site Experiments

Canonical log for the reduced fast-iteration decentralized SUMO study on:

- `./config/dublin_voronoi_fast_8.json`

Selected connected subset:

- `95`, `94`, `418`, `419`, `612`, `925`, `60`, `202`

Associated Voronoi subset map:

- `./data/TrafficGeneration/dublin_march_2025/voronoi_site_cells_fast_8_map.html`

## 2026-04-13: Dublin-Only `routeSampler.py` Baseline, Reduced 8-Site Subset

- Command:
  - `./.venv/bin/python scripts/evaluate_routesampler_baseline.py --output ./output/routesampler/dublin_fast_8_routesampler_baseline.json`
- Finished cleanly:
  - yes
- Output written:
  - `./output/routesampler/dublin_fast_8_routesampler_baseline.json`
- Key metrics:
  - mean `profile_mae`: about `171.00`
  - mean `profile_rmse`: about `294.78`
  - best baseline sites by `profile_mae`: `418` and `95`, both effectively `0.00`
  - worst baseline site by `profile_mae`: site `60`, about `1181.63`
- Study role:
  - Dublin-only SUMO-tool baseline for paper-aligned comparison against the best faithful decentralized 8-site DesRUTGe run

## 2026-04-13: Dublin-Only Volume-Affinity Faithful Validation, `r=5`, `1/1/1`

- Command:
  - `UV_CACHE_DIR=.uv-cache uv run --no-sync python ./src/main_sim_decentralized.py -r 5 -t ./config/dublin_voronoi_fast_8_volume_affinity.json -a Mean -db Traffic_Generator --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ --trafficSimulationMode sumo --trafficTotalTimesteps 1 --trafficEpisodeMaxSteps 1 --trafficTestEpisodes 1 -o ./output/decentralized_sim/dublin_fast_8_volume_affinity_r5_smoke.json`
- Finished cleanly:
  - yes
- Output written:
  - `./output/decentralized_sim/dublin_fast_8_volume_affinity_r5_smoke.json`
- Key metrics by round:
  - round `1`: mean `profile_mae` about `126.77`, mean reward about `0.5625`
  - round `2`: mean `profile_mae` about `131.94`, mean reward about `0.5365`
  - round `3`: mean `profile_mae` about `136.68`, mean reward about `0.4948`
  - round `4`: mean `profile_mae` about `142.48`, mean reward about `0.4896`
  - round `5`: mean `profile_mae` about `147.59`, mean reward about `0.4896`
- Study role:
  - Dublin-only model-exchange validation using neighbor sets induced by volume affinity instead of Voronoi adjacency

## 2026-04-13: Dublin-Only Pattern-Affinity Faithful Validation, `r=5`, `1/1/1`

- Command:
  - `UV_CACHE_DIR=.uv-cache uv run --no-sync python ./src/main_sim_decentralized.py -r 5 -t ./config/dublin_voronoi_fast_8_pattern_affinity.json -a Mean -db Traffic_Generator --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ --trafficSimulationMode sumo --trafficTotalTimesteps 1 --trafficEpisodeMaxSteps 1 --trafficTestEpisodes 1 -o ./output/decentralized_sim/dublin_fast_8_pattern_affinity_r5_smoke.json`
- Parent-reported worker completion:
  - about `3121.28s`
- Finished cleanly:
  - yes
- Output written:
  - `./output/decentralized_sim/dublin_fast_8_pattern_affinity_r5_smoke.json`
- Key metrics by round:
  - round `1`: mean `profile_mae` about `123.19`, mean reward about `0.6302`
  - round `2`: mean `profile_mae` about `122.40`, mean reward about `0.7083`
  - round `3`: mean `profile_mae` about `124.63`, mean reward about `0.5781`
  - round `4`: mean `profile_mae` about `126.95`, mean reward about `0.4844`
  - round `5`: mean `profile_mae` about `129.33`, mean reward about `0.5365`
- Study role:
  - Dublin-only model-exchange validation using neighbor sets induced by daily-profile pattern affinity instead of Voronoi adjacency

## 2026-03-24: Restored-Contract Real SUMO Smoke, `r=1`, `1/1/1`

- Command:
  - `UV_CACHE_DIR=.uv-cache uv run --no-sync python ./src/main_sim_decentralized.py -r 1 -t ./config/dublin_voronoi_fast_8.json -a Mean -db Traffic_Generator --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ --trafficSimulationMode sumo --trafficTotalTimesteps 1 --trafficEpisodeMaxSteps 1 --trafficTestEpisodes 1 -o ./output/decentralized_sim/dublin_fast_8_hourly_sumo_r1_smoke.json`
- Recorded UTC start before launch:
  - `2026-03-24T16:40:19Z`
- Recorded UTC end:
  - `2026-03-24T16:51:15Z`
- Wall-clock duration:
  - about `10m56s`
- Parent-reported worker completion:
  - about `626.03s`
- Finished cleanly:
  - yes
- Output written:
  - `./output/decentralized_sim/dublin_fast_8_hourly_sumo_r1_smoke.json`
- Lingering Python or `sumo` processes:
  - none observed after completion
- Key metrics:
  - mean `profile_mae`: about `122.36`
  - mean `profile_rmse`: about `133.96`
  - mean reward: about `0.7083`
  - `R-Squared`: about `0.99999998`
  - highest `profile_mae`: site `60`, about `743.15`
  - lowest `profile_mae`: site `612`, about `0.30`
- Runtime notes:
  - all `8/8` sites remained active through the broad evaluation phase
  - no severe straggler tail comparable to the 18-site `57` behavior appeared
  - the slowest round completion was site `60` at about `625.91s`

## 2026-03-24: Restored-Contract Real SUMO Smoke, `r=2`, `1/1/1`

- Command:
  - `UV_CACHE_DIR=.uv-cache uv run --no-sync python ./src/main_sim_decentralized.py -r 2 -t ./config/dublin_voronoi_fast_8.json -a Mean -db Traffic_Generator --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ --trafficSimulationMode sumo --trafficTotalTimesteps 1 --trafficEpisodeMaxSteps 1 --trafficTestEpisodes 1 -o ./output/decentralized_sim/dublin_fast_8_hourly_sumo_r2_smoke.json`
- Recorded UTC start before launch:
  - `2026-03-24T16:52:31Z`
- Recorded UTC end:
  - `2026-03-24T17:16:54.584371Z`
- Wall-clock duration:
  - about `24m24s`
- Parent-reported worker completion:
  - about `1242.87s`
- Finished cleanly:
  - yes
- Output written:
  - `./output/decentralized_sim/dublin_fast_8_hourly_sumo_r2_smoke.json`
- Lingering Python or `sumo` processes:
  - none observed after completion
- Key metrics by round:
  - round `1`: mean `profile_mae` about `125.06`, mean `profile_rmse` about `136.75`, mean reward about `0.6719`, `R-Squared` about `0.99999252`
  - round `2`: mean `profile_mae` about `126.45`, mean `profile_rmse` about `138.00`, mean reward about `0.5990`, `R-Squared` about `0.99998761`
  - worst site by `profile_mae` in both rounds: site `60`, about `752.69` then `754.82`
  - best site by `profile_mae`: site `612` in round `1` at about `0.26`; site `418` in round `2` at about `0.49`
- Runtime notes:
  - this trainer evaluates after every federated round, so `r=2` roughly doubled wall time versus `r=1`
  - round-level skew now matters: site `612` reached round `1` training early and then spent about `125.39s` waiting at the next barrier
  - despite that barrier skew, the run still completed cleanly without the pathological 18-site-style tail

## 2026-03-24: Restored-Contract Real SUMO Smoke, `r=4`, `1/1/1`

- Command:
  - `UV_CACHE_DIR=.uv-cache uv run --no-sync python ./src/main_sim_decentralized.py -r 4 -t ./config/dublin_voronoi_fast_8.json -a Mean -db Traffic_Generator --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ --trafficSimulationMode sumo --trafficTotalTimesteps 1 --trafficEpisodeMaxSteps 1 --trafficTestEpisodes 1 -o ./output/decentralized_sim/dublin_fast_8_hourly_sumo_r4_smoke.json`
- Recorded UTC start before launch:
  - `2026-03-24T21:07:41Z`
- Recorded UTC end:
  - `2026-03-24T21:49:36.133126Z`
- Wall-clock duration:
  - about `41m55s`
- Parent-reported worker completion:
  - about `2499.37s`
- Finished cleanly:
  - yes
- Output written:
  - `./output/decentralized_sim/dublin_fast_8_hourly_sumo_r4_smoke.json`
- Lingering Python or `sumo` processes:
  - none observed after completion
- Key metrics by round:
  - round `1`: mean `profile_mae` about `123.07`, mean `profile_rmse` about `134.46`, mean reward about `0.6563`, `R-Squared` about `0.99999222`
  - round `2`: mean `profile_mae` about `125.15`, mean `profile_rmse` about `136.50`, mean reward about `0.4635`, `R-Squared` about `0.99998689`
  - round `3`: mean `profile_mae` about `128.14`, mean `profile_rmse` about `139.92`, mean reward about `0.4167`, `R-Squared` about `0.99998809`
  - round `4`: mean `profile_mae` about `129.14`, mean `profile_rmse` about `141.16`, mean reward about `0.3385`, `R-Squared` about `0.99999098`
  - worst site by `profile_mae` in every round: site `60`, about `739.40` down to `718.99`
  - best site by `profile_mae` in every round: site `612`, about `0.61` up to `3.14`
- Runtime notes:
  - the trainer still evaluates after every federated round, so wall time continued to grow roughly with round count
  - barrier skew remained present across later rounds:
    - `612` reached later rounds early and waited about `129.77s`, `79.75s`, and `87.84s` at successive barriers
  - the run still finished cleanly with no 18-site-style pathological long tail

## 2026-03-24: Restored-Contract Real SUMO Smoke, `r=5`, `1/1/1`

- Command:
  - `UV_CACHE_DIR=.uv-cache uv run --no-sync python ./src/main_sim_decentralized.py -r 5 -t ./config/dublin_voronoi_fast_8.json -a Mean -db Traffic_Generator --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ --trafficSimulationMode sumo --trafficTotalTimesteps 1 --trafficEpisodeMaxSteps 1 --trafficTestEpisodes 1 -o ./output/decentralized_sim/dublin_fast_8_hourly_sumo_r5_smoke.json`
- Recorded UTC start before launch:
  - `2026-03-24T21:49:44Z`
- Recorded UTC end:
  - `2026-03-24T22:44:02.146844Z`
- Wall-clock duration:
  - about `54m18s`
- Finished cleanly:
  - yes
- Output written:
  - `./output/decentralized_sim/dublin_fast_8_hourly_sumo_r5_smoke.json`
- Lingering Python or `sumo` processes:
  - none observed after completion
- Key metrics by round:
  - round `1`: mean `profile_mae` about `123.92`, mean `profile_rmse` about `135.27`, mean reward about `0.5938`, `R-Squared` about `0.99999868`
  - round `2`: mean `profile_mae` about `126.37`, mean `profile_rmse` about `137.87`, mean reward about `0.4479`, `R-Squared` about `0.99999612`
  - round `3`: mean `profile_mae` about `127.63`, mean `profile_rmse` about `139.41`, mean reward about `0.4271`, `R-Squared` about `0.99999344`
  - round `4`: mean `profile_mae` about `130.19`, mean `profile_rmse` about `142.44`, mean reward about `0.3281`, `R-Squared` about `0.99999327`
  - round `5`: mean `profile_mae` about `133.97`, mean `profile_rmse` about `147.29`, mean reward about `0.2760`, `R-Squared` about `0.99999473`
  - worst site by `profile_mae` in every round: site `60`, about `737.07` down to `712.07`
  - best site by `profile_mae` in every round: site `612`, about `0.84` up to `4.71`
- Runtime notes:
  - the full `r=1..5` smoke sweep is now complete
  - later rounds continued to accumulate barrier skew:
    - `612` again reached later rounds earliest and waited about `80.35s` before one of the final aggregations
  - metric drift across rounds is modest but directionally worse:
    - aggregate `profile_mae` and `profile_rmse` rose as rounds increased
    - aggregate reward fell as rounds increased

## 2026-03-24: Completed Smoke Sweep Summary, `r=1..5`, `1/1/1`

- The reduced 8-site real-SUMO smoke sweep is now complete for communication rounds `1` through `5`.
- Wall-clock growth:
  - `r=1`: about `10m56s`
  - `r=2`: about `24m24s`
  - `r=4`: about `41m55s`
  - `r=5`: about `54m18s`
- Main behavioral findings:
  - wall time rises strongly with communication rounds because this trainer performs a full post-aggregation evaluation after every round
  - later rounds increasingly pay synchronization cost because faster nodes finish evaluation early and wait at the next barrier
  - the subset still avoids the extreme pathological single-site tail seen on the 18-site subset
  - aggregate smoke metrics did not improve as rounds increased; they drifted modestly worse instead
- Current recommendation:
  - keep using `./config/dublin_voronoi_fast_8.json` as the fast-iteration path
  - if scaling beyond smoke, do a moderate budget bump on the 8-site subset rather than adding more communication rounds first

## 2026-03-24: Restored-Contract Real SUMO Moderate Run, `r=1`, `5/1/1`

- Command:
  - `UV_CACHE_DIR=.uv-cache uv run --no-sync python ./src/main_sim_decentralized.py -r 1 -t ./config/dublin_voronoi_fast_8.json -a Mean -db Traffic_Generator --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ --trafficSimulationMode sumo --trafficTotalTimesteps 5 --trafficEpisodeMaxSteps 1 --trafficTestEpisodes 1 -o ./output/decentralized_sim/dublin_fast_8_hourly_sumo_r1_tt5_te1.json`
- Recorded UTC start before launch:
  - `2026-03-24T23:07:45Z`
- Recorded UTC end:
  - `2026-03-24T23:31:44.644855463Z`
- Parent-reported worker completion:
  - about `695.46s`
- Finished cleanly:
  - yes
- Output written:
  - `./output/decentralized_sim/dublin_fast_8_hourly_sumo_r1_tt5_te1.json`
- Lingering Python or `sumo` processes:
  - none observed after completion
- Key metrics:
  - mean `profile_mae`: about `122.49`
  - mean `profile_rmse`: about `133.82`
  - mean reward: about `0.6406`
  - `R-Squared`: about `0.99999203`
  - highest `profile_mae`: site `60`, about `736.94`
  - lowest `profile_mae`: site `612`, about `0.20`
- Runtime notes:
  - aggregate profile error was effectively flat versus the `1/1/1`, `r=1` smoke baseline
  - site `612` again reached the barrier first:
    - local training about `71.22s`
    - barrier wait about `48.12s`

## 2026-03-24: Restored-Contract Real SUMO Moderate Run, `r=2`, `5/1/1`

- Command:
  - `UV_CACHE_DIR=.uv-cache uv run --no-sync python ./src/main_sim_decentralized.py -r 2 -t ./config/dublin_voronoi_fast_8.json -a Mean -db Traffic_Generator --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ --trafficSimulationMode sumo --trafficTotalTimesteps 5 --trafficEpisodeMaxSteps 1 --trafficTestEpisodes 1 -o ./output/decentralized_sim/dublin_fast_8_hourly_sumo_r2_tt5_te1.json`
- Recorded UTC start before launch:
  - `2026-03-24T23:31:55Z`
- Recorded UTC end:
  - `2026-03-24T23:57:37.851764108Z`
- Parent-reported worker completion:
  - about `1390.13s`
- Finished cleanly:
  - yes
- Output written:
  - `./output/decentralized_sim/dublin_fast_8_hourly_sumo_r2_tt5_te1.json`
- Lingering Python or `sumo` processes:
  - none observed after completion
- Key metrics by round:
  - round `1`: mean `profile_mae` about `128.64`, mean `profile_rmse` about `140.45`, mean reward about `0.5052`
  - round `2`: mean `profile_mae` about `132.98`, mean `profile_rmse` about `145.16`, mean reward about `0.4427`
- Runtime notes:
  - increasing to `r=2` made aggregate metrics clearly worse than `r=1` at the same `5/1/1` budget
  - site `612` again reached barriers much earlier than the slower nodes:
    - round `0` barrier wait about `48.15s`
    - round `1` barrier wait about `86.76s`

## 2026-03-24 to 2026-03-25: Restored-Contract Real SUMO Moderate Run, `r=1`, `10/2/1`

- Command:
  - `UV_CACHE_DIR=.uv-cache uv run --no-sync python ./src/main_sim_decentralized.py -r 1 -t ./config/dublin_voronoi_fast_8.json -a Mean -db Traffic_Generator --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ --trafficSimulationMode sumo --trafficTotalTimesteps 10 --trafficEpisodeMaxSteps 2 --trafficTestEpisodes 1 -o ./output/decentralized_sim/dublin_fast_8_hourly_sumo_r1_tt10_te1_step2.json`
- Recorded UTC start before launch:
  - `2026-03-24T23:59:01Z`
- Recorded UTC end:
  - `2026-03-25T01:17:12.640453400Z`
- Parent-reported worker completion:
  - about `1369.86s`
- Finished cleanly:
  - yes
- Output written:
  - `./output/decentralized_sim/dublin_fast_8_hourly_sumo_r1_tt10_te1_step2.json`
- Lingering Python or `sumo` processes:
  - none observed after completion
- Key metrics:
  - mean `profile_mae`: about `126.63`
  - mean `profile_rmse`: about `138.16`
  - mean reward: about `0.6615`
  - `R-Squared`: about `0.99999191`
  - highest `profile_mae`: site `60`, about `759.32`
  - lowest `profile_mae`: site `612`, about `0.20`
- Runtime notes:
  - this budget is materially more expensive than `5/1/1` while not improving aggregate error
  - round-0 skew grew:
    - site `612` local training about `142.33s`
    - site `612` barrier wait about `95.05s`
    - most other nodes trained in about `232-237s`

## 2026-03-25: Restored-Contract Real SUMO Moderate Run, `r=2`, `10/2/1`

- Command:
  - `UV_CACHE_DIR=.uv-cache uv run --no-sync python ./src/main_sim_decentralized.py -r 2 -t ./config/dublin_voronoi_fast_8.json -a Mean -db Traffic_Generator --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ --trafficSimulationMode sumo --trafficTotalTimesteps 10 --trafficEpisodeMaxSteps 2 --trafficTestEpisodes 1 -o ./output/decentralized_sim/dublin_fast_8_hourly_sumo_r2_tt10_te1_step2.json`
- Recorded UTC start before launch:
  - `2026-03-25T01:17:20Z`
- Recorded UTC end:
  - `2026-03-25T02:03:35.606589955Z`
- Parent-reported worker completion:
  - about `2746.15s`
- Finished cleanly:
  - yes
- Output written:
  - `./output/decentralized_sim/dublin_fast_8_hourly_sumo_r2_tt10_te1_step2.json`
- Lingering Python or `sumo` processes:
  - none observed after completion
- Key metrics by round:
  - round `1`: mean `profile_mae` about `130.12`, mean `profile_rmse` about `142.62`, mean reward about `0.5417`
  - round `2`: mean `profile_mae` about `142.66`, mean `profile_rmse` about `156.83`, mean reward about `0.4323`
  - worst site by `profile_mae` in both rounds: site `60`, about `752.49` then `769.61`
  - best site by `profile_mae` in both rounds: site `612`, about `1.29` then `2.49`
- Runtime notes:
  - this is the clearest sign yet that more rounds are not paying off on the current VM
  - round-1 barrier waits became large enough to dominate the runtime of early finishers:

## 2026-04-13: Dublin `routeSampler.py` Baseline On The Reduced 8-Site Subset

- Command:
  - `./.venv/bin/python ./scripts/evaluate_routesampler_baseline.py -output ./output/routesampler/dublin_fast_8_routesampler_baseline.json`
- Scope:
  - faithful Dublin-only baseline on sites `95`, `94`, `418`, `419`, `612`, `925`, `60`, `202`
  - same daily-profile metric contract used by the reduced 8-site DesRUTGe runs
- Finished cleanly:
  - yes
- Output written:
  - `./output/routesampler/dublin_fast_8_routesampler_baseline.json`
- Baseline notes:
  - the helper builds oversized candidate route files from each Dublin site's existing corridor route and then applies SUMO's `routeSampler.py` against hourly edge-count targets
  - several simpler corridor sites matched almost exactly under this baseline
  - the heaviest corridors remained materially harder for `routeSampler.py`, especially site `60`
- Key metrics:
  - mean `profile_mae`: about `171.00`
  - mean `profile_rmse`: about `294.78`
  - strongest baseline sites by `profile_mae`:
    - `95`: `0.00`
    - `418`: `0.00`
    - `612`: `0.00`
  - weakest baseline sites by `profile_mae`:
    - `60`: about `1181.63`
    - `419`: about `128.75`
    - `202`: about `57.42`
- Comparison note:
  - the current best faithful reduced-subset decentralized run remains `./output/decentralized_sim/dublin_fast_8_hourly_sumo_r1_smoke.json`
  - on mean `profile_mae`, that DesRUTGe point stayed below the new `routeSampler.py` baseline

## 2026-04-13: Volume-Affinity Neighbor Validation, `r=5`, `1/1/1`

- Topology:
  - `./config/dublin_voronoi_fast_8_volume_affinity.json`
- Cluster structure:
  - cluster `0`: `95`, `94`, `418`, `612`, `925`
  - cluster `1`: `419`, `202`
  - cluster `2`: `60`
- Command:
  - `UV_CACHE_DIR=.uv-cache uv run --no-sync python ./src/main_sim_decentralized.py -r 5 -t ./config/dublin_voronoi_fast_8_volume_affinity.json -a Mean -db Traffic_Generator --trafficDataPath ./data/TrafficGeneration/dublin_march_2025/ --trafficSimulationMode sumo --trafficTotalTimesteps 1 --trafficEpisodeMaxSteps 1 --trafficTestEpisodes 1 -o ./output/decentralized_sim/dublin_fast_8_volume_affinity_r5_smoke.json`
- Finished cleanly:
  - yes
- Output written:
  - `./output/decentralized_sim/dublin_fast_8_volume_affinity_r5_smoke.json`
- Worker completion:
  - about `3103.61s`
- Key metrics by round:
  - round `1`: mean `profile_mae` about `126.77`, mean reward about `0.5625`
  - round `2`: mean `profile_mae` about `131.94`, mean reward about `0.5365`
  - round `3`: mean `profile_mae` about `136.68`, mean reward about `0.4948`
  - round `4`: mean `profile_mae` about `142.48`, mean reward about `0.4896`
  - round `5`: mean `profile_mae` about `147.59`, mean reward about `0.4896`
- Runtime notes:
  - this affinity strategy completed all five faithful rounds on Dublin-only data
  - the singleton high-volume cluster left site `60` with no neighbors, making this a materially different exchange structure than the geographic topology
  - degradation across rounds remained directionally worse rather than better, matching the broader reduced-subset pattern
    - site `612`: about `646.85s`
    - site `418`: about `574.94s`
    - site `95`: about `531.95s`
    - site `94`: about `343.75s`
    - site `202`: about `292.99s`
  - aggregate metrics degraded from round `1` to round `2` despite the extra cost

## 2026-03-25: Moderate-Budget Summary, `5/1/1` and `10/2/1`

- The moderate 8-site decentralized study is now complete for:
  - `5/1/1` at `r=1` and `r=2`
  - `10/2/1` at `r=1` and `r=2`
- Main findings:
  - raising rounds from `r=1` to `r=2` made aggregate metrics worse at both moderate budgets
  - `10/2/1` cost substantially more runtime than `5/1/1`, but did not improve aggregate profile error
  - site `60` remained the worst site by `profile_mae`
  - site `612` remained the fastest node locally, but that mostly translated into larger barrier waits as round count increased
- Current recommendation:
  - do not prioritize decentralized `r=3` on the current VM
  - if `r=3` is ever run, treat it as a deliberate degradation/round-overhead study rather than an optimization candidate
  - use `8siteCentralizedExperiments.md` as the companion log for the completed server-95 centralized comparison set
