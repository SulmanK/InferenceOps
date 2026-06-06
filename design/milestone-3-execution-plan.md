# Milestone 3 Execution Plan: Heuristic Controllers

## Purpose

Milestone 3 turns routing policy into the benchmark target. Milestone 2 proved that the harness can replay deterministic traces through SGLang Gateway and collect raw policy results. Milestone 3 adds bounded controllers that choose among supported policies and evaluates whether those choices improve or hurt observed latency.

## V0 Scope

The first Milestone 3 pass is offline and deterministic:

- Normalize Milestone 2 policy/scenario summaries into one comparison artifact.
- Define a bounded controller action: `set_policy` to one of `round_robin`, `cache_aware`, or `power_of_two`.
- Implement static baselines and simple heuristic controllers.
- Compare controller choices against the best observed policy per scenario.
- Report regret in milliseconds against the best observed p95 latency.

This pass does not mutate a live router during replay. Live control intervals can be added after the offline evaluator is stable.

## Commands

Build the normalized comparison from a Milestone 2 run:

```bash
python metrics/compare_m2_policies.py \
  --run-id 20260606T192505Z \
  --replay-dir artifacts/m2/replay \
  --out-dir results/milestone3
```

Evaluate controllers:

```bash
python controllers/evaluate_m3_controllers.py \
  --comparison results/milestone3/policy_comparison_20260606T192505Z.json \
  --out-dir results/milestone3
```

## Done Means

- Controller actions are finite and validated.
- Static policies are evaluated as baselines.
- At least one heuristic controller is evaluated.
- The output includes per-scenario selected policy, best observed policy, p95 latency, and regret.
- The report explains where the heuristic wins or loses.

## Next Live Step

After offline evaluation, add a live controller runner that:

- Starts SGLang Gateway with an initial policy.
- Replays one trace segment.
- Reads normalized metrics.
- Applies a bounded policy change at a fixed control interval.
- Records action history and invalid action count.
