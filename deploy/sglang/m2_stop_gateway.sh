#!/usr/bin/env bash
set -euo pipefail

if [ -f logs/sglang_gateway.pid ]; then
  kill "$(cat logs/sglang_gateway.pid)" >/dev/null 2>&1 || true
  rm -f logs/sglang_gateway.pid
fi

pkill -f "sglang_router.launch_router" >/dev/null 2>&1 || true

echo "SGLang Gateway stopped."

