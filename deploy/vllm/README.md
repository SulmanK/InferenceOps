# Milestone 0: vLLM Baseline

This directory contains the first serving backend workflow for InferenceOps.

## Backend Choice

Milestone 0 uses vLLM because it is a production-oriented LLM serving platform with an OpenAI-compatible API and built-in benchmark tooling.

## Run

On a Linux GPU host:

```bash
bash deploy/vllm/m0_wsl_preflight.sh
bash deploy/vllm/m0_setup_vllm.sh
bash deploy/vllm/m0_serve_vllm.sh
```

In a second shell:

```bash
bash deploy/vllm/m0_benchmark_vllm.sh
```

The benchmark script writes to `artifacts/m0/` and runs `metrics/summarize_m0.py` at the end.

## WSL Notes

WSL2 is a valid way to run vLLM on Windows when the GPU is compatible. Run the preflight script inside WSL before installing dependencies:

```bash
bash deploy/vllm/m0_wsl_preflight.sh
```

Current vLLM NVIDIA wheels require a newer GPU than Pascal-era cards such as GTX 1060. If the preflight fails on compute capability, keep using this workspace for development and run Milestone 0 on a compatible local or cloud GPU.

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `MODEL` | `Qwen/Qwen2.5-1.5B-Instruct` | Hugging Face model ID |
| `PORT` | `8000` | vLLM server port |
| `API_KEY` | `local-dev` | Local API key |
| `REQUEST_RATE` | `2` | Benchmark request rate |
| `NUM_PROMPTS` | `100` | Benchmark request count |
| `INPUT_LEN` | `512` | Random dataset input length |
| `OUTPUT_LEN` | `128` | Random dataset output length |
