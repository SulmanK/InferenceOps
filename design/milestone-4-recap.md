# Milestone 4 Recap: Agentic Controller Offline Start

## What Was Added

Milestone 4 now has an offline agentic controller path.

New files:

- `controllers/agentic_policy.py`
- `controllers/evaluate_m4_agentic.py`
- `tests/test_agentic_policy.py`
- `design/milestone-4-execution-plan.md`

## Design

The agent receives a compact JSON observation and must return:

```json
{
  "policy": "cache_aware",
  "reason": "short explanation"
}
```

Allowed policies:

- `round_robin`
- `cache_aware`
- `power_of_two`

Any unsupported policy, malformed JSON, or missing reason triggers the safe fallback policy. This keeps the agentic controller inside the same bounded action space as the heuristic controller.

## Scripted Offline Evaluation

Source run: `20260606T192505Z`

Agent mode: `scripted`

Artifacts:

```text
artifacts/m4/offline-agentic
```

Results:

| Scenario | Agent Policy | Best Policy | Valid | Fallback | P95 ms | Best P95 ms | Regret ms |
|---|---|---|---:|---:|---:|---:|---:|
| `degraded_worker` | `power_of_two` | `cache_aware` | true | false | 195.58 | 195.37 | 0.21 |
| `mixed_short_long` | `power_of_two` | `power_of_two` | true | false | 287.92 | 287.92 | 0.00 |
| `shared_prefix_burst` | `cache_aware` | `cache_aware` | true | false | 193.33 | 193.33 | 0.00 |

The scripted agent validates the agentic control path and matches the Milestone 3 heuristic behavior on this trace pack. It does not yet prove that a real LLM improves on the heuristic baseline.

## OpenAI-Compatible Offline Evaluation

Source run: `20260606T192505Z`

Agent mode: `openai-compatible`

Artifacts:

```text
artifacts/m4/offline-agentic
```

Results:

| Scenario | Agent Policy | Best Policy | Valid | Fallback | P95 ms | Best P95 ms | Regret ms |
|---|---|---|---:|---:|---:|---:|---:|
| `degraded_worker` | `cache_aware` | `cache_aware` | true | false | 195.37 | 195.37 | 0.00 |
| `mixed_short_long` | `power_of_two` | `power_of_two` | true | false | 287.92 | 287.92 | 0.00 |
| `shared_prefix_burst` | `cache_aware` | `cache_aware` | true | false | 193.33 | 193.33 | 0.00 |

The OpenAI-compatible agent produced valid bounded actions for every scenario, used no fallbacks, and matched the best observed policy for all three scenarios on this replay artifact.

## Current Status

Milestone 4 is complete for offline v0. The agentic-controller plumbing works in scripted and real OpenAI-compatible modes, and the real agent matched the best observed policy on the current three-scenario policy matrix.

No Lambda instance is required yet.
