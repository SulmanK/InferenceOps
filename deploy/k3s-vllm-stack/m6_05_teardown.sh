#!/usr/bin/env bash
set -euo pipefail

RELEASE="${RELEASE:-vllm}"
NAMESPACE="${NAMESPACE:-default}"

export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"

if [ -f logs/m6_port_forward.pid ]; then
  kill "$(cat logs/m6_port_forward.pid)" >/dev/null 2>&1 || true
  rm -f logs/m6_port_forward.pid
fi

helm --kubeconfig "${KUBECONFIG}" uninstall "${RELEASE}" -n "${NAMESPACE}" || true
echo "Milestone 6 vLLM release removed. k3s cluster remains installed."
