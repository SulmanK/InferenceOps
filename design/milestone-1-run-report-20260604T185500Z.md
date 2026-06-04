# Milestone 1 Run Report

## Run Metadata

| Field | Value |
|---|---|
| Run ID | `20260604T185500Z` |
| Date | 2026-06-04 |
| Milestone | M1 deterministic trace replay |
| Cloud/provider | Lambda Cloud |
| GPU | NVIDIA H100 PCIe, 81559 MiB |
| Driver/CUDA | NVIDIA driver 580.105.08, CUDA 13.0 |
| Backend | vLLM 0.22.0 |
| Model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Endpoint | `http://127.0.0.1:8000/v1/chat/completions` |

## Trace

| Field | Value |
|---|---|
| Trace | `traces/pack_v1/shared_prefix_burst.jsonl` |
| Trace SHA256 | `53b60a1de9d5ad49f03d12a54cabd11d3a8712b92d121f5dd266e05785c96b51` |
| Records | 48 |
| Time scale | 1.0 |
| Prompt generator | `m1_trace_generator_v1` |

## Results

| Metric | Value |
|---|---:|
| Requests | 48 |
| Successful | 48 |
| Failed | 0 |
| Replay duration | 26.01 s |
| Latency p50 | 401.49 ms |
| Latency p95 | 439.18 ms |
| Latency p99 | 1132.82 ms |
| Mean latency | 431.65 ms |
| Completion tokens | 6131 |

## Artifact Paths

| Artifact | Path |
|---|---|
| Replay summary | `artifacts/m1/replay/replay_summary_20260604T185500Z.json` |
| Replay results | `artifacts/m1/replay/replay_results_20260604T185500Z.jsonl` |
| vLLM log | `artifacts/m1/replay/vllm_20260604T185500Z.log` |
| Trace manifest | `traces/pack_v1/manifest.json` |

## Notes

- This run proves the Milestone 1 replay harness can execute a deterministic JSONL trace against a real OpenAI-compatible vLLM endpoint.
- The first request included cold path overhead relative to the rest of the replay, which is visible in the p99 latency.
- The replay harness currently records end-to-end request latency, status, and OpenAI usage fields. TTFT/TPOT remain covered by the Milestone 0 vLLM benchmark path; streaming token timing can be added later if needed.

