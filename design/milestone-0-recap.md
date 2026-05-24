# Milestone 0 Recap

## What We Did

Milestone 0 established the first real serving baseline for InferenceOps.

We used Lambda Cloud because the local Windows/WSL machine can see the GTX 1060, but that GPU has compute capability 6.1 and is below current vLLM wheel requirements. Lambda provided a compatible Linux GPU VM with an NVIDIA A10.

Steps completed:

- Connected to the Lambda instance over SSH with the `.pem` key.
- Verified the GPU with `nvidia-smi`.
- Copied the InferenceOps workspace to the VM.
- Installed `uv`, Python 3.12, vLLM, PyTorch/CUDA dependencies, and benchmark dependencies.
- Started a vLLM OpenAI-compatible server.
- Served `Qwen/Qwen2.5-1.5B-Instruct`.
- Ran the Milestone 0 serving benchmark against `http://127.0.0.1:8000`.
- Captured benchmark output, metadata, GPU telemetry, and vLLM logs.
- Copied the artifact bundle back into the local workspace.
- Fixed the summary parser so GPU telemetry fields are included.
- Stopped the vLLM process on the Lambda instance.

## Run Details

| Field | Value |
|---|---|
| Run ID | `20260524T194907Z` |
| Cloud | Lambda Cloud |
| GPU | NVIDIA A10, 23028 MiB |
| Driver/CUDA | NVIDIA driver 580.105.08, CUDA 13.0 |
| Backend | vLLM 0.21.0 |
| Model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Dataset | random |
| Requests | 100 |
| Input length | 512 tokens |
| Output length | 128 tokens |
| Request rate | 2 req/s |

## Results

| Metric | Value |
|---|---:|
| Successful requests | 100 |
| Failed requests | 0 |
| Request throughput | 1.956 req/s |
| Output throughput | 250.37 tok/s |
| Total token throughput | 1251.86 tok/s |
| TTFT p50 | 43.82 ms |
| TTFT p95 | 64.91 ms |
| TTFT p99 | 127.17 ms |
| TPOT p50 | 8.68 ms |
| TPOT p95 | 9.40 ms |
| TPOT p99 | 9.67 ms |
| GPU utilization avg / max | 70.88% / 100% |
| Max GPU memory used | 21083 MiB |
| Avg GPU power | 124.68 W |

## Local Artifacts

| Artifact | Path |
|---|---|
| Filled run report | `design/milestone-0-run-report-20260524T194907Z.md` |
| Normalized summary | `artifacts/m0/summary_20260524T194907Z.json` |
| Benchmark JSON | `artifacts/m0/openai-2.0qps-Qwen2.5-1.5B-Instruct-20260524-195005.json` |
| GPU telemetry | `artifacts/m0/nvidia_smi_20260524T194907Z.csv` |
| vLLM log | `artifacts/m0/vllm_20260524T194907Z.log` |
| Metadata | `artifacts/m0/metadata_20260524T194907Z.json` |
| Models response | `artifacts/m0/models_20260524T194907Z.json` |

## Current Status

Milestone 0 is complete. InferenceOps now has a real production-serving baseline on vLLM with reproducible artifacts.

Next milestone: **Milestone 1, deterministic trace generation and replay**.

Before starting Milestone 1:

- Keep the Lambda instance terminated unless actively running experiments.
- Commit the source files and small reports.
- Decide whether large raw artifacts should stay local only or be stored with Git LFS / external storage later.

