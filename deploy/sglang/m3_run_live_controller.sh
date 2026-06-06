#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-0.5B-Instruct}"
CONTROLLER="${CONTROLLER:-scenario_heuristic}"
TRACE_MANIFEST="${TRACE_MANIFEST:-traces/pack_v1/manifest.json}"
OUT_DIR="${OUT_DIR:-artifacts/m3/live}"
GATEWAY_PORT="${GATEWAY_PORT:-30000}"
WORKER1_PORT="${WORKER1_PORT:-31001}"
WORKER2_PORT="${WORKER2_PORT:-31002}"
TIME_SCALE="${TIME_SCALE:-1.0}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

mkdir -p "${OUT_DIR}" logs

bash deploy/sglang/m2_wait_for_endpoint.sh "http://127.0.0.1:${WORKER1_PORT}/v1/models" 900
bash deploy/sglang/m2_wait_for_endpoint.sh "http://127.0.0.1:${WORKER2_PORT}/v1/models" 900

python controllers/run_live_controller.py \
  --controller "${CONTROLLER}" \
  --manifest "${TRACE_MANIFEST}" \
  --model "${MODEL}" \
  --base-url "http://127.0.0.1:${GATEWAY_PORT}" \
  --out "${OUT_DIR}" \
  --run-id "${RUN_ID}" \
  --time-scale "${TIME_SCALE}" \
  --gateway-port "${GATEWAY_PORT}" \
  --worker1-port "${WORKER1_PORT}" \
  --worker2-port "${WORKER2_PORT}"

echo "Milestone 3 live controller run complete: ${RUN_ID} (${CONTROLLER})"
