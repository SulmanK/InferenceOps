# Milestone 2 Recap: SGLang Gateway Router Benchmark

## What Ran

Milestone 2 validated a real two-worker SGLang serving topology behind SGLang Model Gateway.

Topology:

```text
replay_trace_pack.py -> SGLang Gateway :30000
                         -> SGLang worker 1 :31001
                         -> SGLang worker 2 :31002
```

Run ID: `20260606T192505Z`

Model: `Qwen/Qwen2.5-0.5B-Instruct`

Trace pack: `traces/pack_v1/manifest.json`

Policies:

- `round_robin`
- `cache_aware`
- `power_of_two`

## Setup Notes

The initial SGLang install only provided the main `sglang` package. SGLang Model Gateway required the separate `sglang-router` package, so `deploy/sglang/m2_setup_sglang.sh` now installs both packages.

The initial two-worker launch also failed because each worker tried to reserve too much GPU memory for KV/cache. `deploy/sglang/m2_start_workers.sh` now launches each worker with:

```bash
--mem-fraction-static 0.25
--max-total-tokens 131072
```

With those limits, both workers became healthy on the H100 instance.

## Results

All policy/scenario runs completed successfully: 9 runs, 432 total requests, 0 failures.

| Policy | Scenario | Requests | Failed | P50 ms | P95 ms | P99 ms | Duration s |
|---|---:|---:|---:|---:|---:|---:|---:|
| `cache_aware` | `degraded_worker` | 48 | 0 | 166.34 | 195.37 | 195.55 | 28.87 |
| `cache_aware` | `mixed_short_long` | 48 | 0 | 146.98 | 288.97 | 289.61 | 31.38 |
| `cache_aware` | `shared_prefix_burst` | 48 | 0 | 171.01 | 193.33 | 197.41 | 13.16 |
| `power_of_two` | `degraded_worker` | 48 | 0 | 158.51 | 195.58 | 196.81 | 28.82 |
| `power_of_two` | `mixed_short_long` | 48 | 0 | 147.30 | 287.92 | 288.87 | 31.22 |
| `power_of_two` | `shared_prefix_burst` | 48 | 0 | 171.53 | 193.49 | 195.20 | 13.13 |
| `round_robin` | `degraded_worker` | 48 | 0 | 174.18 | 196.72 | 199.17 | 29.01 |
| `round_robin` | `mixed_short_long` | 48 | 0 | 148.17 | 289.63 | 296.50 | 31.47 |
| `round_robin` | `shared_prefix_burst` | 48 | 0 | 178.68 | 196.92 | 231.26 | 13.29 |

## Artifacts

Local artifacts were copied into:

```text
artifacts/m2/
artifacts/m2/replay/
```

Key files:

- `artifacts/m2/metadata_20260606T192505Z.json`
- `artifacts/m2/replay/trace_pack_replay_summary_20260606T192505Z_round_robin.json`
- `artifacts/m2/replay/trace_pack_replay_summary_20260606T192505Z_cache_aware.json`
- `artifacts/m2/replay/trace_pack_replay_summary_20260606T192505Z_power_of_two.json`

## Current State

The SGLang Gateway and worker processes were stopped on the Lambda VM after the run.

Milestone 2 is functionally complete for the v0 router benchmark: the project now has a reproducible SGLang Gateway policy matrix over deterministic trace replay.

## Next Step

Milestone 3 should build controller/policy comparison on top of these artifacts. The immediate engineering work is to normalize policy outputs into one comparison table and add simple heuristic controllers that can be evaluated deterministically against the same trace pack.
