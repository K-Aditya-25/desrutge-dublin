# Experiment Summary

This file summarizes the completed experiments currently recorded in the repo logs. It focuses on completed runs only and separates historical scalar-era results from the current restored hourly-contract results.

## 18-Site Experiments

Topology: `config/dublin_voronoi_first_cloud_18.json`

| Study | Mode | Date | Budget | Rounds | Output | Runtime | Headline metrics | Main takeaway |
|---|---|---:|---|---:|---|---|---|---|
| Historical scalar baseline | Decentralized `sumo` | pre-restored phase | `1/1/1` | 1 | `output/decentralized_sim/dublin_first_cloud_18_mean_r1_smoke.json` | about `223s` | mean absolute scalar error `22.46`, mean relative scalar error `3.32%` | Valid scalar-era baseline only; not part of the current trainer contract |
| Historical scalar ramp | Decentralized `sumo` | pre-restored phase | `5/1/1` | 1 | `output/decentralized_sim/dublin_first_cloud_18_mean_r1_tt5_te1.json` | about `372s` | mean absolute scalar error `22.28` | More training cost with essentially no scalar-quality improvement |
| Restored-contract validation | Decentralized `test` | restored phase | `1/1/1` | 1 | `output/decentralized_sim/dublin_first_cloud_18_profile_test_r1_smoke.json` | about `11.17s` worker completion | mean `profile_mae` `203.73`, mean `profile_rmse` `223.63` | First end-to-end restored-contract validation; surrogate backend only |
| Restored hourly-refactor validation | Decentralized `test` | restored hourly refactor | `1/1/1` | 1 | `output/decentralized_sim/dublin_first_cloud_18_profile_test_r1_smoke_refactored.json` | not emphasized in log | mean `profile_mae` `205.20`, mean `profile_rmse` `225.35` | Hourly refactor preserved end-to-end decentralized behavior |
| Restored real SUMO baseline | Decentralized `sumo` | 2026-03-23 | `1/1/1` | 1 | `output/decentralized_sim/dublin_first_cloud_18_hourly_sumo_r1_smoke.json` | about `24m35s` | mean `profile_mae` `296.49`, mean `profile_rmse` `336.01`, mean reward `0.3981` | First trusted real restored-contract baseline; site `57` is the dominant straggler |
| Restored real SUMO ramp | Decentralized `sumo` | 2026-03-23 | `10/2/1` | 1 | `output/decentralized_sim/dublin_first_cloud_18_hourly_sumo_r1_tt10_te1_step2.json` | about `47m15s` | mean `profile_mae` `288.01`, mean `profile_rmse` `327.05`, mean reward `0.4352` | Nearly doubled runtime for only slight aggregate improvement |

## 8-Site Decentralized Experiments

Topology: `config/dublin_voronoi_fast_8.json`

| Study | Mode | Date | Budget | Rounds | Output | Runtime | Headline metrics | Main takeaway |
|---|---|---:|---|---:|---|---|---|---|
| Smoke baseline | Decentralized `sumo` | 2026-03-24 | `1/1/1` | 1 | `output/decentralized_sim/dublin_fast_8_hourly_sumo_r1_smoke.json` | about `10m56s` | mean `profile_mae` `122.36`, mean `profile_rmse` `133.96`, mean reward `0.7083` | Strong fast-iteration baseline |
| Smoke round scaling | Decentralized `sumo` | 2026-03-24 | `1/1/1` | 2 | `output/decentralized_sim/dublin_fast_8_hourly_sumo_r2_smoke.json` | about `24m24s` | round 1 mean `profile_mae` `125.06`, mean reward `0.6719`; round 2 mean `profile_mae` `126.45`, mean reward `0.5990` | More rounds increased cost and slightly worsened results |
| Smoke round scaling | Decentralized `sumo` | 2026-03-24 | `1/1/1` | 4 | `output/decentralized_sim/dublin_fast_8_hourly_sumo_r4_smoke.json` | about `41m55s` | round 1 reward `0.6563`; round 2 reward `0.4635`; round 3 reward `0.4167`; round 4 mean `profile_mae` `129.14`, mean reward `0.3385` | Barrier skew becomes material in later rounds |
| Smoke round scaling | Decentralized `sumo` | 2026-03-24 | `1/1/1` | 5 | `output/decentralized_sim/dublin_fast_8_hourly_sumo_r5_smoke.json` | about `54m18s` | round 1 reward `0.5938`; round 2 reward `0.4479`; round 3 reward `0.4271`; round 4 reward `0.3281`; round 5 mean `profile_mae` `133.97`, mean reward `0.2760` | Full smoke sweep confirms degradation with additional rounds |
| Moderate budget | Decentralized `sumo` | 2026-03-24 | `5/1/1` | 1 | `output/decentralized_sim/dublin_fast_8_hourly_sumo_r1_tt5_te1.json` | about `23m59s` | mean `profile_mae` `122.49`, mean `profile_rmse` `133.82`, mean reward `0.6406` | Similar aggregate error to smoke baseline at higher cost |
| Moderate budget | Decentralized `sumo` | 2026-03-24 | `5/1/1` | 2 | `output/decentralized_sim/dublin_fast_8_hourly_sumo_r2_tt5_te1.json` | about `25m43s` | round 1 mean `profile_mae` `128.64`, mean reward `0.5052`; round 2 mean `profile_mae` `132.98`, mean reward `0.4427` | `r=2` is clearly worse than `r=1` at the same budget |
| Larger moderate budget | Decentralized `sumo` | 2026-03-24 to 2026-03-25 | `10/2/1` | 1 | `output/decentralized_sim/dublin_fast_8_hourly_sumo_r1_tt10_te1_step2.json` | about `1h18m` | mean `profile_mae` `126.63`, mean `profile_rmse` `138.16`, mean reward `0.6615` | More expensive without aggregate profile-error improvement |
| Larger moderate budget | Decentralized `sumo` | 2026-03-25 | `10/2/1` | 2 | `output/decentralized_sim/dublin_fast_8_hourly_sumo_r2_tt10_te1_step2.json` | about `46m16s` | round 1 mean `profile_mae` `130.12`, mean reward `0.5417`; round 2 mean `profile_mae` `142.66`, mean reward `0.4323` | Strong evidence that extra rounds do not pay off on the current setup |

## 8-Site Centralized Experiments

Topology: `config/dublin_centralized_fast_8_server_95.json`

Important note: centralized outputs in this repo keep only server statistics.

| Study | Mode | Date | Budget | Rounds | Output | Runtime | Headline metrics | Main takeaway |
|---|---|---:|---|---:|---|---|---|---|
| Smoke baseline | Centralized, server-only export | 2026-03-25 | `1/1/1` | 1 | `output/centralized_sim/dublin_fast_8_centralized_server95_r1_smoke.json` | about `11m25s` | reward `0.8333`, `profile_mae` `4.7004`, `profile_rmse` `6.0616` | Good single-round server result |
| Smoke round scaling | Centralized, server-only export | 2026-03-25 | `1/1/1` | 2 | `output/centralized_sim/dublin_fast_8_centralized_server95_r2_smoke.json` | about `36m10s` | round 1 reward `0.7917`, `profile_mae` `4.7838`; round 2 reward `0.6667`, `profile_mae` `7.2421` | Same round-scaling degradation pattern as decentralized mode |
| Moderate budget | Centralized, server-only export | 2026-03-25 | `5/1/1` | 1 | `output/centralized_sim/dublin_fast_8_centralized_server95_r1_tt5_te1.json` | about `1h02m09s` | reward `1.0`, `profile_mae` `0.7361`, `profile_rmse` `0.9556` | One of the strongest centralized single-round points |
| Moderate budget | Centralized, server-only export | 2026-03-25 | `5/1/1` | 2 | `output/centralized_sim/dublin_fast_8_centralized_server95_r2_tt5_te1.json` | about `23m32s` | round 1 reward `0.75`, `profile_mae` `5.3671`; round 2 reward `0.625`, `profile_mae` `9.7421` | `r=2` degrades sharply relative to `r=1` |
| Larger moderate budget | Centralized, server-only export | 2026-03-25 | `10/2/1` | 1 | `output/centralized_sim/dublin_fast_8_centralized_server95_r1_tt10_te1_step2.json` | about `23m15s` | reward `1.0`, `profile_mae` `0.7361`, `profile_rmse` `0.9556` | Matches the best centralized single-round result |
| Larger moderate budget | Centralized, server-only export | 2026-03-25 | `10/2/1` | 2 | `output/centralized_sim/dublin_fast_8_centralized_server95_r2_tt10_te1_step2.json` | about `3h00m06s` | round 1 reward `1.0`, `profile_mae` `4.0615`; round 2 reward `0.7083`, `profile_mae` `10.6448` | Heavy barrier domination at higher cost |

## Findings

- The 18-site study proves the restored hourly SUMO-backed pipeline works, but it is runtime-heavy and dominated by stragglers, especially site `57`.
- The older 18-site scalar runs are useful runtime history, but they are not valid current baselines because they predate the restored hourly contract.
- The reduced 8-site subset is the practical experimental platform for fast iteration.
- On the 8-site decentralized study, increasing communication rounds consistently increased runtime and slightly worsened aggregate profile metrics.
- Moderate budget increases on the 8-site decentralized study did not improve aggregate profile quality enough to justify their extra cost.
- The 8-site subset avoided the pathological 18-site-style tail, but still showed meaningful synchronization and barrier-wait skew, especially from early finishers such as site `612`.
- The 8-site centralized comparison shows the same directional round-scaling degradation as decentralized mode.
- The strongest centralized results are the single-round moderate settings on server `95`, but those results are server-only and are not directly comparable to full multi-site decentralized aggregate summaries.
- Across the completed runs currently recorded in the repo, there is no evidence yet that adding more communication rounds improves results on the current VM setup.
- The current best practical recommendation is to treat single-round 8-site experiments as the main comparison path and to prioritize analysis of completed runs over pushing to higher round counts.

## Sources

- `18siteExperiments.md`
- `8siteExperiments.md`
- `8siteCentralizedExperiments.md`
- `RunningSummary.md`
- `progress.md`
