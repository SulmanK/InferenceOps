#!/usr/bin/env bash
set -euo pipefail

bash deploy/sglang/m2_stop_gateway.sh || true

for pid_file in logs/sglang_worker1.pid logs/sglang_worker2.pid; do
  if [ -f "${pid_file}" ]; then
    kill "$(cat "${pid_file}")" >/dev/null 2>&1 || true
    rm -f "${pid_file}"
  fi
done

pkill -f "sglang.launch_server" >/dev/null 2>&1 || true

echo "SGLang workers stopped."

