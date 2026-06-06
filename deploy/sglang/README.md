# Milestone 2: SGLang Gateway

This directory contains the Milestone 2 workflow for running two SGLang workers behind SGLang Model Gateway.

SGLang Gateway is the router under test. The replay client sends traffic to the gateway, and the gateway forwards requests to workers according to the selected policy.

## Default Topology

```text
replay_trace_pack.py -> SGLang Gateway :30000
                         -> worker 1 :31001
                         -> worker 2 :31002
```

Defaults:

| Variable | Default |
|---|---|
| `MODEL` | `Qwen/Qwen2.5-0.5B-Instruct` |
| `WORKER1_PORT` | `31001` |
| `WORKER2_PORT` | `31002` |
| `GATEWAY_PORT` | `30000` |
| `POLICIES` | `round_robin,cache_aware,power_of_two` |

The Milestone 2 default model is smaller than Milestone 0/1 because we run two workers at once.

## Lambda Run

On a compatible Lambda GPU instance:

```bash
bash deploy/sglang/m2_setup_sglang.sh
bash deploy/sglang/m2_start_workers.sh
bash deploy/sglang/m2_run_policy_matrix.sh
```

Copy back:

```text
artifacts/m2/
logs/
```

Stop processes when finished:

```bash
bash deploy/sglang/m2_stop_sglang.sh
```

Then terminate the Lambda instance in the console.

## Single Policy Run

Start workers:

```bash
bash deploy/sglang/m2_start_workers.sh
```

Start gateway:

```bash
POLICY=cache_aware bash deploy/sglang/m2_start_gateway.sh
```

Replay through gateway:

```bash
python replay/replay_trace_pack.py \
  --manifest traces/pack_v1/manifest.json \
  --base-url http://127.0.0.1:30000 \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --out artifacts/m2/replay \
  --run-id m2_cache_aware \
  --time-scale 1.0
```

## Official Docs

- SGLang Model Gateway: https://docs.sglang.ai/advanced_features/router.html
- SGLang install docs: https://docs.sglang.ai/get_started/install.html
