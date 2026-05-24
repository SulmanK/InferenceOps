# Milestone 0 Run Report

## Run Metadata

| Field | Value |
|---|---|
| Run ID | `20260524T194907Z` |
| Date | 2026-05-24 |
| Backend | vLLM |
| Model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Model revision | default Hugging Face revision |
| GPU SKU | NVIDIA A10, 23028 MiB |
| Cloud/provider | Lambda Cloud |
| Driver/CUDA | NVIDIA driver 580.105.08, CUDA 13.0 |
| vLLM version | 0.21.0 |

## Benchmark Configuration

| Field | Value |
|---|---|
| Dataset | random |
| Input length | 512 |
| Output length | 128 |
| Request rate | 2 req/s |
| Number of prompts | 100 |
| Warmup | 0 |

## Results

| Metric | Value |
|---|---:|
| Successful requests | 100 |
| Failed requests | 0 |
| TTFT p50 | 43.82 ms |
| TTFT p95 | 64.91 ms |
| TTFT p99 | 127.17 ms |
| TPOT p50 | 8.68 ms |
| TPOT p95 | 9.40 ms |
| TPOT p99 | 9.67 ms |
| Mean ITL | 8.75 ms |
| ITL p95 | 9.13 ms |
| Request throughput | 1.956 req/s |
| Output tok/s | 250.37 |
| Total tok/s | 1251.86 |
| Total input tokens | 51200 |
| Total output tokens | 12800 |
| Max GPU memory used | 21083 MiB |
| Avg GPU utilization | 70.88% |
| Max GPU utilization | 100.00% |
| Avg GPU power | 124.68 W |

## Artifact Paths

| Artifact | Path |
|---|---|
| Models response JSON | `artifacts/m0/models_20260524T194907Z.json` |
| Benchmark JSON | `artifacts/m0/openai-2.0qps-Qwen2.5-1.5B-Instruct-20260524-195005.json` |
| GPU telemetry CSV | `artifacts/m0/nvidia_smi_20260524T194907Z.csv` |
| Metadata JSON | `artifacts/m0/metadata_20260524T194907Z.json` |
| Normalized summary JSON | `artifacts/m0/summary_20260524T194907Z.json` |
| vLLM log | `artifacts/m0/vllm_20260524T194907Z.log` |

## Notes

- First Milestone 0 baseline completed on Lambda Cloud with a single NVIDIA A10.
- The vLLM server successfully loaded `Qwen/Qwen2.5-1.5B-Instruct` and exposed `/v1/models` plus completion routes.
- The benchmark completed 100/100 requests with no failures at 2 req/s.
- This is a baseline artifact, not a tuned performance result.
