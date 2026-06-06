#!/usr/bin/env bash
set -euo pipefail

POLICY="${POLICY:-cache_aware}"
HOST="${HOST:-0.0.0.0}"
GATEWAY_PORT="${GATEWAY_PORT:-30000}"
WORKER1_PORT="${WORKER1_PORT:-31001}"
WORKER2_PORT="${WORKER2_PORT:-31002}"
LOG_DIR="${LOG_DIR:-logs}"

mkdir -p "${LOG_DIR}" artifacts/m2/replay

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

echo "Starting SGLang Gateway"
echo "  policy:  ${POLICY}"
echo "  gateway: ${HOST}:${GATEWAY_PORT}"
echo "  workers: http://127.0.0.1:${WORKER1_PORT} http://127.0.0.1:${WORKER2_PORT}"

nohup python -m sglang_router.launch_router \
  --worker-urls "http://127.0.0.1:${WORKER1_PORT}" "http://127.0.0.1:${WORKER2_PORT}" \
  --policy "${POLICY}" \
  --host "${HOST}" \
  --port "${GATEWAY_PORT}" \
  > "${LOG_DIR}/sglang_gateway_${POLICY}.log" 2>&1 &
echo "$!" > "${LOG_DIR}/sglang_gateway.pid"

echo "Gateway starting. Watch log with:"
echo "  tail -f ${LOG_DIR}/sglang_gateway_${POLICY}.log"

