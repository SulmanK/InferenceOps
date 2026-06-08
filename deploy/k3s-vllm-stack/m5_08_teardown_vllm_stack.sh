#!/usr/bin/env bash
set -euo pipefail

RELEASE="${RELEASE:-vllm}"
NAMESPACE="${NAMESPACE:-default}"
LOG_DIR="${LOG_DIR:-logs}"

export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"

if [ -f "${LOG_DIR}/m5_port_forward.pid" ]; then
  old_pid="$(cat "${LOG_DIR}/m5_port_forward.pid")"
  kill "${old_pid}" >/dev/null 2>&1 || true
  rm -f "${LOG_DIR}/m5_port_forward.pid"
fi

helm --kubeconfig "${KUBECONFIG}" uninstall "${RELEASE}" -n "${NAMESPACE}" || true

echo "vLLM stack release removed. k3s itself is left installed intentionally."
