#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-default}"
SERVICE="${SERVICE:-vllm-router-service}"
LOCAL_PORT="${LOCAL_PORT:-30080}"
SERVICE_PORT="${SERVICE_PORT:-80}"
LOG_DIR="${LOG_DIR:-logs}"

export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
mkdir -p artifacts/m5 "${LOG_DIR}"

if [ -f "${LOG_DIR}/m5_port_forward.pid" ]; then
  old_pid="$(cat "${LOG_DIR}/m5_port_forward.pid")"
  kill "${old_pid}" >/dev/null 2>&1 || true
fi

nohup sudo k3s kubectl port-forward -n "${NAMESPACE}" "svc/${SERVICE}" "${LOCAL_PORT}:${SERVICE_PORT}" \
  > "${LOG_DIR}/m5_port_forward.log" 2>&1 &
echo "$!" > "${LOG_DIR}/m5_port_forward.pid"

for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${LOCAL_PORT}/v1/models" >/dev/null 2>&1; then
    curl -fsS "http://127.0.0.1:${LOCAL_PORT}/v1/models" | tee artifacts/m5/vllm_stack_models.json
    echo "port-forward ready on http://127.0.0.1:${LOCAL_PORT}"
    exit 0
  fi
  sleep 5
done

echo "timed out waiting for vLLM Production Stack service"
tail -n 80 "${LOG_DIR}/m5_port_forward.log" || true
exit 1
