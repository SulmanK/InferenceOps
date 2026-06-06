#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-0.5B-Instruct}"
HOST="${HOST:-0.0.0.0}"
WORKER1_PORT="${WORKER1_PORT:-31001}"
WORKER2_PORT="${WORKER2_PORT:-31002}"
LOG_DIR="${LOG_DIR:-logs}"
MEM_FRACTION_STATIC="${MEM_FRACTION_STATIC:-0.25}"
MAX_TOTAL_TOKENS="${MAX_TOTAL_TOKENS:-131072}"

mkdir -p "${LOG_DIR}" artifacts/m2/replay

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

echo "Starting SGLang workers"
echo "  model:   ${MODEL}"
echo "  worker1: ${HOST}:${WORKER1_PORT}"
echo "  worker2: ${HOST}:${WORKER2_PORT}"
echo "  memory:  mem_fraction_static=${MEM_FRACTION_STATIC} per worker"
echo "  tokens:  max_total_tokens=${MAX_TOTAL_TOKENS} per worker"

nohup python -m sglang.launch_server \
  --model-path "${MODEL}" \
  --host "${HOST}" \
  --port "${WORKER1_PORT}" \
  --mem-fraction-static "${MEM_FRACTION_STATIC}" \
  --max-total-tokens "${MAX_TOTAL_TOKENS}" \
  > "${LOG_DIR}/sglang_worker1.log" 2>&1 &
echo "$!" > "${LOG_DIR}/sglang_worker1.pid"

nohup python -m sglang.launch_server \
  --model-path "${MODEL}" \
  --host "${HOST}" \
  --port "${WORKER2_PORT}" \
  --mem-fraction-static "${MEM_FRACTION_STATIC}" \
  --max-total-tokens "${MAX_TOTAL_TOKENS}" \
  > "${LOG_DIR}/sglang_worker2.log" 2>&1 &
echo "$!" > "${LOG_DIR}/sglang_worker2.pid"

echo "Workers starting. Watch logs with:"
echo "  tail -f ${LOG_DIR}/sglang_worker1.log"
echo "  tail -f ${LOG_DIR}/sglang_worker2.log"
