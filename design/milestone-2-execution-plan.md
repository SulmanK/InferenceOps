# Milestone 2 Execution Plan

## Goal

Run two real SGLang workers behind SGLang Model Gateway and compare routing policies using the existing `traces/pack_v1` replay workload.

Milestone 2 is the first router benchmark. The gateway, not the model worker alone, is the system under test.

## Current Plan

Use a single large Lambda GPU instance first. An H100 is easiest because it can comfortably colocate two small workers. The default Milestone 2 model is:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

This is intentionally smaller than the Milestone 0/1 model because two workers run simultaneously.

## Topology

```text
replay_trace_pack.py
  -> SGLang Model Gateway :30000
      -> SGLang worker 1 :31001
      -> SGLang worker 2 :31002
```

## Local Prep

Validate traces and local code before renting GPU time:

```bash
python replay/validate_trace.py traces/pack_v1/shared_prefix_burst.jsonl traces/pack_v1/mixed_short_long.jsonl traces/pack_v1/degraded_worker.jsonl
python -m unittest discover -s tests
```

## Lambda Run

On the Lambda instance:

```bash
bash deploy/sglang/m2_setup_sglang.sh
bash deploy/sglang/m2_start_workers.sh
bash deploy/sglang/m2_run_policy_matrix.sh
```

Defaults:

```text
MODEL=Qwen/Qwen2.5-0.5B-Instruct
POLICIES=round_robin,cache_aware,power_of_two
TIME_SCALE=1.0
```

To use a smaller or different policy set:

```bash
POLICIES=round_robin,cache_aware bash deploy/sglang/m2_run_policy_matrix.sh
```

## Outputs

Expected outputs:

```text
artifacts/m2/metadata_<run_id>.json
artifacts/m2/replay/trace_pack_replay_summary_<run_id>_<policy>.json
artifacts/m2/replay/replay_summary_<run_id>_<policy>_<scenario>.json
artifacts/m2/replay/replay_results_<run_id>_<policy>_<scenario>.jsonl
artifacts/m2/replay/sglang_gateway_<run_id>_<policy>.log
logs/sglang_worker1.log
logs/sglang_worker2.log
```

Copy back `artifacts/m2/` and worker/gateway logs before terminating the instance.

## Done Means

- Two SGLang workers start successfully.
- SGLang Gateway routes to both workers.
- `traces/pack_v1` replays through the gateway.
- At least two routing policies are compared.
- Artifacts and logs are copied back locally.
- A Milestone 2 report compares scenario and policy results.

## References

- SGLang Model Gateway: https://docs.sglang.io/advanced_features/sgl_model_gateway.html
- SGLang install docs: https://sgl-project.github.io/get_started/install.html

