# 8-Site Centralized Experiments

Canonical log for the reduced fast-iteration centralized SUMO study on:

- `./config/dublin_centralized_fast_8_server_95.json`

Server-centered star subset:

- server `95`
- clients `94`, `418`, `419`, `612`, `925`, `60`, `202`

Important export note:

- centralized mode in this repo still evaluates after every round
- the final output JSON keeps only the server statistics, as returned from `src/simulator/simulation.py`

## 2026-03-25: Smoke, `r=1`, `1/1/1`

- Output:
  - `./output/centralized_sim/dublin_fast_8_centralized_server95_r1_smoke.json`
- UTC start:
  - `2026-03-25T11:22:04Z`
- UTC end:
  - `2026-03-25T11:33:28.554869969Z`
- Wall time:
  - about `11m25s`
- Worker completion:
  - about `624.85s`
- Server-only metrics:
  - reward `0.8333`
  - `profile_mae` about `4.7004`
  - `profile_rmse` about `6.0616`

## 2026-03-25: Smoke, `r=2`, `1/1/1`

- Output:
  - `./output/centralized_sim/dublin_fast_8_centralized_server95_r2_smoke.json`
- UTC start:
  - `2026-03-25T11:33:59Z`
- UTC end:
  - `2026-03-25T12:10:08.797306909Z`
- Wall time:
  - about `36m10s`
- Worker completion:
  - about `1246.74s`
- Server-only metrics by round:
  - round `1`: reward `0.7917`, `profile_mae` about `4.7838`, `profile_rmse` about `6.1822`
  - round `2`: reward `0.6667`, `profile_mae` about `7.2421`, `profile_rmse` about `9.3351`

## 2026-03-25: Moderate, `r=1`, `5/1/1`

- Output:
  - `./output/centralized_sim/dublin_fast_8_centralized_server95_r1_tt5_te1.json`
- UTC start:
  - `2026-03-25T12:10:26Z`
- UTC end:
  - `2026-03-25T13:12:34.862739046Z`
- Wall time:
  - about `1h02m09s`
- Worker completion:
  - about `695.27s`
- Server-only metrics:
  - reward `1.0`
  - `profile_mae` about `0.7361`
  - `profile_rmse` about `0.9556`

## 2026-03-25: Moderate, `r=2`, `5/1/1`

- Output:
  - `./output/centralized_sim/dublin_fast_8_centralized_server95_r2_tt5_te1.json`
- UTC start:
  - `2026-03-25T17:15:47Z`
- UTC end:
  - `2026-03-25T17:39:19.039685580Z`
- Wall time:
  - about `23m32s`
- Worker completion:
  - about `1393.75s`
- Server-only metrics by round:
  - round `1`: reward `0.75`, `profile_mae` about `5.3671`, `profile_rmse` about `6.9675`
  - round `2`: reward `0.625`, `profile_mae` about `9.7421`, `profile_rmse` about `12.6429`

## 2026-03-25: Moderate, `r=1`, `10/2/1`

- Output:
  - `./output/centralized_sim/dublin_fast_8_centralized_server95_r1_tt10_te1_step2.json`
- UTC start:
  - `2026-03-25T17:39:35Z`
- UTC end:
  - `2026-03-25T18:02:50.454702519Z`
- Wall time:
  - about `23m15s`
- Worker completion:
  - about `1368.12s`
- Server-only metrics:
  - reward `1.0`
  - `profile_mae` about `0.7361`
  - `profile_rmse` about `0.9556`

## 2026-03-25: Moderate, `r=2`, `10/2/1`

- Output:
  - `./output/centralized_sim/dublin_fast_8_centralized_server95_r2_tt10_te1_step2.json`
- UTC start:
  - `2026-03-25T18:03:04Z`
- UTC end:
  - `2026-03-25T21:03:09.915230779Z`
- Wall time:
  - about `3h00m06s`
- Worker completion:
  - about `2740.42s`
- Server-only metrics by round:
  - round `1`: reward `1.0`, `profile_mae` about `4.0615`, `profile_rmse` about `5.3278`
  - round `2`: reward `0.7083`, `profile_mae` about `10.6448`, `profile_rmse` about `16.0976`
- Runtime notes:
  - round-1 barrier waits became very large:
    - site `612` about `654.90s`
    - site `418` about `578.92s`
    - site `94` about `465.80s`

## 2026-03-25: Centralized Summary

- Completed centralized references now exist for smoke plus `5/1/1` and `10/2/1` at `r=1` and `r=2`.
- The same directional round-scaling degradation seen in decentralized mode also appears here.
- Centralized synchronization was tighter than decentralized at smoke and `5/1/1`, but by `10/2/1`, `r=2` it was also heavily barrier-dominated.
- The strongest server-only centralized points were still the single-round moderate settings:
  - `5/1/1`, `r=1`
  - `10/2/1`, `r=1`
  - both gave site `95` reward `1.0`, `profile_mae` about `0.7361`, `profile_rmse` about `0.9556`
