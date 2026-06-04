# Milestone 1 Execution Plan

## Goal

Build deterministic trace generation and replay so InferenceOps moves from one-off benchmark commands to reproducible workload packs.

Milestone 1 should run locally first. A GPU is only needed after the trace and replay code validates locally.

## Local Run

Generate the first trace pack:

```bash
python replay/generate_trace_pack.py --out traces/pack_v1 --seed 42 --count 48
```

Validate it:

```bash
python replay/validate_trace.py traces/pack_v1/*.jsonl
```

Run local tests:

```bash
python -m unittest
```

## GPU Replay Run

After local validation, start the Milestone 0 vLLM server on Lambda again and replay the whole trace pack:

```bash
python replay/replay_trace_pack.py \
  --manifest traces/pack_v1/manifest.json \
  --base-url http://127.0.0.1:8000 \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --out artifacts/m1/replay \
  --time-scale 1.0
```

To replay only one trace:

```bash
python replay/replay_trace.py \
  --trace traces/pack_v1/shared_prefix_burst.jsonl \
  --base-url http://127.0.0.1:8000 \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --out artifacts/m1/replay \
  --time-scale 1.0
```

Use `--time-scale 0` for a quick functional smoke test. Use `--time-scale 1.0` for real arrival timing.

Run a local dry-run before renting GPU time:

```bash
python replay/replay_trace_pack.py --manifest traces/pack_v1/manifest.json --out artifacts/m1/replay --time-scale 0 --dry-run
```

## Done Means

- Trace pack manifest exists with hashes.
- Each JSONL trace validates against the schema.
- Replay can send a trace to an OpenAI-compatible endpoint.
- Replay emits per-request result JSONL and summary JSON.
- The same trace can be rerun against vLLM with stable metadata and artifact paths.
