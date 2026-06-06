# Milestone 3 Recap: First Heuristic Controller Baseline

## What Was Added

Milestone 3 now has an offline controller evaluation layer on top of the Milestone 2 SGLang Gateway results.

New source files:

- `metrics/compare_m2_policies.py`
- `controllers/policies.py`
- `controllers/evaluate_m3_controllers.py`
- `tests/test_controllers.py`
- `design/milestone-3-execution-plan.md`

## Current Scope

This first pass is deterministic and offline. It does not yet mutate a live SGLang Gateway during replay.

The bounded action space is:

```text
set_policy in {round_robin, cache_aware, power_of_two}
```

Implemented controllers:

- `static_round_robin`
- `static_cache_aware`
- `static_power_of_two`
- `scenario_heuristic`
- `tail_guard`

## Verification Run

Source Milestone 2 run: `20260606T192505Z`

Temporary verification outputs were written to:

```text
C:\tmp\InferenceOps-m3
```

The repo artifact directory had a Windows path issue when creating new subdirectories from Python, so verification output was kept in `C:\tmp` for now. The source code and design docs are in the repo.

## Initial Controller Result

Metric: p95 latency regret against the best observed policy for each scenario.

| Controller | Scenario | Chosen Policy | Best Policy | P95 ms | Best P95 ms | Regret ms |
|---|---|---|---|---:|---:|---:|
| `scenario_heuristic` | `degraded_worker` | `power_of_two` | `cache_aware` | 195.58 | 195.37 | 0.21 |
| `scenario_heuristic` | `mixed_short_long` | `power_of_two` | `power_of_two` | 287.92 | 287.92 | 0.00 |
| `scenario_heuristic` | `shared_prefix_burst` | `cache_aware` | `cache_aware` | 193.33 | 193.33 | 0.00 |

The first heuristic is already close to the observed oracle on this trace pack. The degraded-worker scenario chose `power_of_two`, while the best observed p95 was narrowly `cache_aware` by `0.21 ms`, which is likely within run noise and should be retested before drawing a strong conclusion.

## Next Step

## Live Controller Run

Run ID: `20260606T194927Z`

Controller: `scenario_heuristic`

Mode: live SGLang Gateway, one bounded policy decision per scenario.

Actions:

| Scenario | Selected Policy | Reason |
|---|---|---|
| `shared_prefix_burst` | `cache_aware` | prefer cache locality for repeated-prefix traffic |
| `mixed_short_long` | `power_of_two` | protect short requests from long-prefill imbalance |
| `degraded_worker` | `power_of_two` | prefer load-sensitive routing when a worker looks degraded |

Results:

| Scenario | Requests | Failed | P50 ms | P95 ms | P99 ms | Duration s |
|---|---:|---:|---:|---:|---:|---:|
| `shared_prefix_burst` | 48 | 0 | 168.21 | 197.93 | 200.60 | 13.19 |
| `mixed_short_long` | 48 | 0 | 149.29 | 293.51 | 298.59 | 31.36 |
| `degraded_worker` | 48 | 0 | 183.45 | 196.58 | 196.88 | 29.12 |

Live artifacts were copied locally to:

```text
C:\tmp\InferenceOps-m3-live
```

The live run proves the controller path can control a real SGLang Gateway with finite actions and deterministic scenario boundaries.

## Next Step

The next Milestone 3 step should add a finer live controller runner:

- Start Gateway with an initial policy.
- Replay trace segments.
- Observe normalized latency/error state.
- Change policy only at fixed control intervals.
- Record action history, invalid action count, and policy-switch count.
