#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
API_KEY="${API_KEY:-local-dev}"
RESULT_DIR="${RESULT_DIR:-artifacts/m0}"
REQUEST_RATE="${REQUEST_RATE:-2}"
NUM_PROMPTS="${NUM_PROMPTS:-100}"
INPUT_LEN="${INPUT_LEN:-512}"
OUTPUT_LEN="${OUTPUT_LEN:-128}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"

mkdir -p "${RESULT_DIR}"

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

export OPENAI_API_KEY="${API_KEY}"

echo "Checking vLLM endpoint at ${BASE_URL}/v1/models"
curl -fsS "${BASE_URL}/v1/models" \
  -H "Authorization: Bearer ${API_KEY}" \
  > "${RESULT_DIR}/models_${RUN_ID}.json"

GPU_LOG_PID=""
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi \
    --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.total,power.draw \
    --format=csv -l 1 > "${RESULT_DIR}/nvidia_smi_${RUN_ID}.csv" &
  GPU_LOG_PID="$!"
fi

cleanup() {
  if [ -n "${GPU_LOG_PID}" ]; then
    kill "${GPU_LOG_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

cat > "${RESULT_DIR}/metadata_${RUN_ID}.json" <<EOF
{
  "run_id": "${RUN_ID}",
  "milestone": "m0",
  "backend": "vllm",
  "model": "${MODEL}",
  "base_url": "${BASE_URL}",
  "dataset_name": "random",
  "input_len": ${INPUT_LEN},
  "output_len": ${OUTPUT_LEN},
  "request_rate": ${REQUEST_RATE},
  "num_prompts": ${NUM_PROMPTS}
}
EOF

vllm bench serve \
  --backend openai \
  --base-url "${BASE_URL}" \
  --model "${MODEL}" \
  --dataset-name random \
  --input-len "${INPUT_LEN}" \
  --output-len "${OUTPUT_LEN}" \
  --request-rate "${REQUEST_RATE}" \
  --num-prompts "${NUM_PROMPTS}" \
  --disable-shuffle \
  --save-result \
  --save-detailed \
  --result-dir "${RESULT_DIR}" \
  --percentile-metrics ttft,tpot,itl \
  --metric-percentiles 50,95,99

python metrics/summarize_m0.py "${RESULT_DIR}" --run-id "${RUN_ID}"
