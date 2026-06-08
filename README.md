# InferenceOps

InferenceOps is a reproducible LLM serving benchmark lab for studying how inference systems behave under real operational conditions: deterministic request replay, router policy comparison, controller evaluation, GPU serving, and Kubernetes deployment.

The project started from a single vLLM baseline and grew into a small inference-operations stack using vLLM, SGLang Gateway, heuristic and bounded agentic controllers, and vLLM Production Stack on k3s.

## What This Demonstrates

- Real GPU serving with OpenAI-compatible vLLM endpoints.
- Deterministic trace generation and replay for repeatable workload evaluation.
- Multi-worker routing through SGLang Gateway.
- Static, heuristic, and bounded agentic controller policy evaluation.
- Kubernetes GPU deployment using k3s, Helm, NVIDIA device plugin, and vLLM Production Stack.
- Two-node GPU cluster debugging, including private-network k3s routing and local PVC scheduling constraints.
- Normalized run artifacts, milestone reports, and benchmark summaries.

## Architecture

```text
traces/pack_v1
  -> replay/replay_trace_pack.py
  -> router or controller
       -> vLLM single backend
       -> SGLang Gateway + workers
       -> vLLM Production Stack on k3s
  -> artifacts + metrics + milestone reports
```

The request plane uses OpenAI-compatible APIs where possible. Backend-specific control still requires adapters or scripts for policy changes, worker health, metrics, route overrides, drain/resume behavior, and unsupported actions.

## Milestones

| Milestone | Focus | Status | Result |
|---|---|---:|---|
| M0 | Single vLLM serving baseline | Complete | 100/100 successful requests on Lambda GPU. |
| M1 | Deterministic trace generation and replay | Complete | `pack_v1` replayed across 3 scenarios with 144/144 successful requests. |
| M2 | SGLang Gateway router benchmark | Complete | 3 policies x 3 scenarios, 432/432 successful requests. |
| M3 | Heuristic controller comparison | Complete | Live bounded controller path completed 144/144 requests. |
| M4 | Optional bounded agentic controller | Complete | Offline agentic policy evaluation against deterministic controller actions. |
| M5 | vLLM Production Stack on single-node k3s | Complete | Kubernetes-deployed vLLM served 144/144 trace requests. |
| M6 | Two-node GPU k3s scaling experiment | Complete | Two vLLM model pods ran across two A100 nodes; trace pack did not saturate enough to show throughput scaling. |

## Results Snapshot

| Run | Backend | Workload | Success | Key metric |
|---|---|---|---:|---|
| M0 `20260524T194907Z` | vLLM | fixed serving benchmark | 100/100 | 1.956 req/s, TTFT p95 64.91 ms |
| M1 `20260604T194800Z` | vLLM | `pack_v1` replay | 144/144 | mixed short/long p95 445.44 ms |
| M2 `20260606T192505Z` | SGLang Gateway | policy matrix | 432/432 | best mixed short/long p95 287.92 ms |
| M3 `20260606T194927Z` | SGLang Gateway | heuristic live controller | 144/144 | bounded scenario-level policy switching |
| M5 `20260608T144831Z` | vLLM Production Stack | k3s single GPU | 144/144 | mixed short/long p95 415.19 ms |
| M6 `20260608T153230Z_fixed` | vLLM Production Stack | k3s two GPU nodes | 144/144 | two model pods across two A100 nodes |

The M6 scaling run is intentionally documented as a systems finding: the two-node deployment worked, but the current trace pack is not heavy enough to prove throughput scaling. A saturation trace pack with higher concurrency and longer outputs is the next step for a stronger scaling result.

## Repository Layout

| Path | Purpose |
|---|---|
| `design/` | Execution plans, milestone recaps, run reports, and design notes. |
| `traces/` | Versioned deterministic workload packs. |
| `replay/` | Trace generation, validation, and replay tools. |
| `controllers/` | Static, heuristic, live, and bounded agentic policy logic. |
| `metrics/` | Comparison and summarization utilities. |
| `deploy/vllm/` | vLLM setup, serving, and baseline benchmark scripts. |
| `deploy/sglang/` | SGLang worker, gateway, and policy-matrix scripts. |
| `deploy/k3s-vllm-stack/` | k3s, NVIDIA device plugin, vLLM Production Stack, and M5/M6 runbooks. |
| `artifacts/` | Local benchmark outputs and collected cluster state. Large generated outputs may be ignored by git. |
| `tests/` | Unit tests for trace and controller tooling. |

## Trace Pack

The first trace pack lives in `traces/pack_v1` and contains three scenarios:

| Scenario | Records | Purpose |
|---|---:|---|
| `shared_prefix_burst` | 48 | Repeated-prefix traffic for cache/locality-sensitive behavior. |
| `mixed_short_long` | 48 | Mixed prompt/output sizes for tail-latency behavior. |
| `degraded_worker` | 48 | Workload shape used for routing and worker-health experiments. |

Trace records include prompt content or deterministic prompt-generation metadata, tokenizer/model details, seeds, prefix groups, arrival times, and input/output targets. Token lengths alone are not treated as sufficient for cache-sensitive evaluation.

## Quickstart: Local Validation

The lightweight parts of the repo can run locally without a GPU:

```bash
python replay/validate_trace.py traces/pack_v1/shared_prefix_burst.jsonl traces/pack_v1/mixed_short_long.jsonl traces/pack_v1/degraded_worker.jsonl
python -m unittest discover -s tests
```

Generate a fresh deterministic trace pack:

```bash
python replay/generate_trace_pack.py --out traces/pack_v1 --seed 42 --count 48
python replay/validate_trace.py traces/pack_v1/*.jsonl
```

## Quickstart: vLLM Baseline

Run this on a Linux GPU host with NVIDIA drivers and a vLLM-compatible GPU:

```bash
bash deploy/vllm/m0_setup_vllm.sh
bash deploy/vllm/m0_serve_vllm.sh
```

In another SSH session:

```bash
bash deploy/vllm/m0_benchmark_vllm.sh
python metrics/summarize_m0.py artifacts/m0
```

The scripts default to `Qwen/Qwen2.5-1.5B-Instruct`, port `8000`, and API key `local-dev`.

## Quickstart: Trace Replay

Once an OpenAI-compatible model endpoint is running:

```bash
python replay/replay_trace.py \
  --trace traces/pack_v1/shared_prefix_burst.jsonl \
  --base-url http://127.0.0.1:8000 \
  --model Qwen/Qwen2.5-1.5B-Instruct
```

Replay the full trace pack:

```bash
python replay/replay_trace_pack.py \
  --manifest traces/pack_v1/manifest.json \
  --base-url http://127.0.0.1:8000 \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --time-scale 1.0
```

## Quickstart: SGLang Gateway

Milestone 2 runs two SGLang workers behind SGLang Gateway and replays `pack_v1` through the gateway:

```bash
bash deploy/sglang/m2_setup_sglang.sh
bash deploy/sglang/m2_start_workers.sh
bash deploy/sglang/m2_run_policy_matrix.sh
```

Controller evaluation:

```bash
python metrics/compare_m2_policies.py
python controllers/evaluate_m3_controllers.py
```

## Quickstart: vLLM Production Stack on k3s

Milestone 5 deploys vLLM Production Stack on a single GPU VM:

```bash
bash deploy/k3s-vllm-stack/m5_00_preflight.sh
bash deploy/k3s-vllm-stack/m5_01_install_k3s_gpu.sh
bash deploy/k3s-vllm-stack/m5_02_install_helm_device_plugin.sh
bash deploy/k3s-vllm-stack/m5_03_validate_gpu_pod.sh
bash deploy/k3s-vllm-stack/m5_04_install_vllm_stack.sh
bash deploy/k3s-vllm-stack/m5_05_port_forward.sh
bash deploy/k3s-vllm-stack/m5_06_replay_trace_pack.sh
bash deploy/k3s-vllm-stack/m5_07_collect_state.sh
```

Milestone 6 extends this to a two-node k3s cluster:

```bash
# server node
SERVER_PRIVATE_IP=<private-ip> SERVER_PUBLIC_IP=<public-ip> \
  bash deploy/k3s-vllm-stack/m6_00_setup_server.sh

# worker node
K3S_URL=https://<server-private-ip>:6443 K3S_TOKEN=<server-token> WORKER_PRIVATE_IP=<worker-private-ip> \
  bash deploy/k3s-vllm-stack/m6_01_setup_worker.sh

# server node
bash deploy/k3s-vllm-stack/m6_02_install_cluster_gpu.sh
bash deploy/k3s-vllm-stack/m6_03_run_scaling_matrix.sh
bash deploy/k3s-vllm-stack/m6_04_collect_cluster_state.sh
```

See `deploy/k3s-vllm-stack/README.md` and `design/milestone-6-execution-plan.md` for details.

## Design Notes

Useful reading order:

1. `design/deep-research-report.md`
2. `design/milestone-0-recap.md`
3. `design/milestone-1-recap.md`
4. `design/milestone-2-recap.md`
5. `design/milestone-3-recap.md`
6. `design/milestone-4-recap.md`
7. `design/milestone-5-recap.md`
8. `design/milestone-6-execution-plan.md`

## Key Lessons

- Reproducible trace replay should come before advanced routing or agentic control.
- OpenAI-compatible request APIs are not the same as backend-agnostic control planes.
- Real infrastructure failures are part of the benchmark: GPU plugin setup, k3s private networking, and PVC node affinity affected results.
- A working two-GPU deployment is not the same as a proven scaling result; the workload must saturate the system.

## Next Work

- Add a saturation trace pack with higher concurrency and longer output targets.
- Capture timestamped GPU utilization during replay.
- Add router-level request distribution metrics.
- Build a compact dashboard for run comparison.
- Optionally test managed Kubernetes if targeting deeper platform/MLOps experience.
