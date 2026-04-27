#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
API_KEY="${API_KEY:-local-dev}"
DTYPE="${DTYPE:-auto}"
LOG_DIR="${LOG_DIR:-logs}"

mkdir -p "${LOG_DIR}"

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

echo "Starting vLLM OpenAI-compatible server"
echo "  model: ${MODEL}"
echo "  host:  ${HOST}"
echo "  port:  ${PORT}"
echo "  log:   ${LOG_DIR}/vllm.log"

vllm serve "${MODEL}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --dtype "${DTYPE}" \
  --api-key "${API_KEY}" \
  > "${LOG_DIR}/vllm.log" 2>&1

