# InferenceOps

InferenceOps is a benchmark harness for evaluating LLM serving control policies on real serving systems.

The current focus is **Milestone 0**: run a production-grade serving backend, send reproducible traffic, and save comparable benchmark artifacts.

## Milestone 0 Backend

Milestone 0 uses **vLLM** as the first serving platform.

Why vLLM:

- It is widely used for production LLM serving.
- It exposes an OpenAI-compatible API.
- It includes serving benchmark tooling.
- It gives us a clean path from a single GPU baseline to later router/control experiments.

## Workspace Layout

| Path | Purpose |
|---|---|
| `design/` | Internal project plans and benchmark specs |
| `deploy/` | Backend launch and benchmark scripts |
| `metrics/` | Artifact normalization and summaries |
| `artifacts/` | Run outputs created by benchmark runs |

## Milestone 0 Quickstart

Milestone 0 is intended to run on a Linux host with a compatible NVIDIA GPU. Since you have Lambda credits, use Lambda first.

See [design/milestone-0-execution-plan.md](design/milestone-0-execution-plan.md) for the recommended cloud GPU execution path.
For Lambda specifically, see [deploy/lambda/README.md](deploy/lambda/README.md).

On the Lambda GPU instance:

```bash
bash deploy/lambda/m0_lambda_bootstrap.sh
bash deploy/vllm/m0_serve_vllm.sh
```

Then, in a second SSH session:

```bash
bash deploy/vllm/m0_benchmark_vllm.sh
```

The lower-level vLLM sequence is:

```bash
bash deploy/vllm/m0_wsl_preflight.sh
bash deploy/vllm/m0_setup_vllm.sh
bash deploy/vllm/m0_serve_vllm.sh
bash deploy/vllm/m0_benchmark_vllm.sh
python metrics/summarize_m0.py artifacts/m0
```

The scripts default to `Qwen/Qwen2.5-1.5B-Instruct`, port `8000`, and API key `local-dev`.

Generated artifacts are written under `artifacts/m0/`.

## Milestone 1 Quickstart

Milestone 1 adds deterministic trace generation and replay.

```bash
python replay/generate_trace_pack.py --out traces/pack_v1 --seed 42 --count 48
python replay/validate_trace.py traces/pack_v1/*.jsonl
python -m unittest
```

Once a vLLM server is running, replay a trace:

```bash
python replay/replay_trace.py --trace traces/pack_v1/shared_prefix_burst.jsonl --base-url http://127.0.0.1:8000
```

Replay the whole trace pack:

```bash
python replay/replay_trace_pack.py --manifest traces/pack_v1/manifest.json --base-url http://127.0.0.1:8000 --time-scale 1.0
```

See [design/milestone-1-execution-plan.md](design/milestone-1-execution-plan.md).

## Milestone 2 Quickstart

Milestone 2 runs two SGLang workers behind SGLang Model Gateway and replays `traces/pack_v1` through the gateway.

```bash
bash deploy/sglang/m2_setup_sglang.sh
bash deploy/sglang/m2_start_workers.sh
bash deploy/sglang/m2_run_policy_matrix.sh
```

See [design/milestone-2-execution-plan.md](design/milestone-2-execution-plan.md) and [design/milestone-2-purpose-sglang.md](design/milestone-2-purpose-sglang.md).

## Milestone 5 Quickstart

Milestone 5 deploys vLLM Production Stack on a single GPU VM using k3s.

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

See [design/milestone-5-execution-plan.md](design/milestone-5-execution-plan.md) and [deploy/k3s-vllm-stack/README.md](deploy/k3s-vllm-stack/README.md).
