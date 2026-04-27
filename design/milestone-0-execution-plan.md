# Milestone 0 Execution Plan

## Decision

Run Milestone 0 on a compatible Linux NVIDIA GPU host, while keeping this Windows/WSL workspace as the source repo.

WSL2 works on this machine, but the local GTX 1060 has compute capability 6.1. Current vLLM NVIDIA wheels require newer hardware, so local vLLM serving is not the right path for this milestone.

## Recommended Path

Use a short-lived cloud GPU VM with one of these GPU classes:

- T4
- L4
- A10
- A100
- RTX 20xx or newer local machine, if available

For Milestone 0, prefer a VM-style provider with SSH access. That keeps the workflow simple: clone the repo, run the scripts, copy artifacts back.

## Run Sequence

On the GPU host:

```bash
git clone <repo-url> InferenceOps
cd InferenceOps

bash deploy/vllm/m0_wsl_preflight.sh
bash deploy/vllm/m0_setup_vllm.sh
```

Start the vLLM server:

```bash
bash deploy/vllm/m0_serve_vllm.sh
```

In a second SSH session:

```bash
cd InferenceOps
bash deploy/vllm/m0_benchmark_vllm.sh
```

Expected output lands in:

```text
artifacts/m0/
```

## Success Criteria

Milestone 0 is complete when `artifacts/m0/` contains:

- `/v1/models` response JSON
- vLLM benchmark JSON
- detailed benchmark output, if emitted by vLLM
- GPU telemetry CSV
- metadata JSON
- normalized summary JSON from `metrics/summarize_m0.py`

Then fill in:

```text
design/milestone-0-run-report-template.md
```

## Defaults

Use the default model first:

```text
Qwen/Qwen2.5-1.5B-Instruct
```

If the GPU has limited memory or setup is tight, use:

```bash
MODEL=Qwen/Qwen2.5-0.5B-Instruct bash deploy/vllm/m0_serve_vllm.sh
MODEL=Qwen/Qwen2.5-0.5B-Instruct bash deploy/vllm/m0_benchmark_vllm.sh
```

Keep the first benchmark small and boring. The goal is not maximum throughput yet; it is a clean, reproducible baseline.

## After Milestone 0

Do not start router work immediately after the first successful run. First:

- inspect the normalized summary
- confirm GPU telemetry was captured
- confirm the run is reproducible with the same parameters
- commit the scripts, report, and one small summary artifact
- keep large raw artifacts out of Git unless intentionally sampled

