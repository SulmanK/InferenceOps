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

Milestone 0 is intended to run on a Linux host with an NVIDIA GPU.

See [design/milestone-0-execution-plan.md](design/milestone-0-execution-plan.md) for the recommended cloud GPU execution path.

```bash
bash deploy/vllm/m0_wsl_preflight.sh
bash deploy/vllm/m0_setup_vllm.sh
bash deploy/vllm/m0_serve_vllm.sh
bash deploy/vllm/m0_benchmark_vllm.sh
python metrics/summarize_m0.py artifacts/m0
```

The scripts default to `Qwen/Qwen2.5-1.5B-Instruct`, port `8000`, and API key `local-dev`.

Generated artifacts are written under `artifacts/m0/`.
