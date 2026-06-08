#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-0.5B-Instruct}"
BASE_URL="${BASE_URL:-http://127.0.0.1:30080}"
TRACE_MANIFEST="${TRACE_MANIFEST:-traces/pack_v1/manifest.json}"
OUT_DIR="${OUT_DIR:-artifacts/m5/replay}"
TIME_SCALE="${TIME_SCALE:-1.0}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"

mkdir -p "${OUT_DIR}" artifacts/m5 logs

python replay/replay_trace_pack.py \
  --manifest "${TRACE_MANIFEST}" \
  --base-url "${BASE_URL}" \
  --model "${MODEL}" \
  --out "${OUT_DIR}" \
  --run-id "${RUN_ID}" \
  --time-scale "${TIME_SCALE}"

cat > "artifacts/m5/metadata_${RUN_ID}.json" <<EOF
{
  "milestone": "m5",
  "run_id": "${RUN_ID}",
  "deployment": "vllm-production-stack-k3s",
  "model": "${MODEL}",
  "base_url": "${BASE_URL}",
  "trace_manifest": "${TRACE_MANIFEST}",
  "time_scale": ${TIME_SCALE}
}
EOF

echo "Milestone 5 replay complete: ${RUN_ID}"
