#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-0.5B-Instruct}"
RELEASE="${RELEASE:-vllm}"
NAMESPACE="${NAMESPACE:-default}"
LOCAL_PORT="${LOCAL_PORT:-30080}"
SERVICE="${SERVICE:-vllm-router-service}"
TRACE_MANIFEST="${TRACE_MANIFEST:-traces/pack_v1/manifest.json}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
M6_CASES="${M6_CASES:-baseline,baseline-pressure,scaling,scaling-pressure}"

export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
mkdir -p artifacts/m6/baseline artifacts/m6/scaling artifacts/m6/k8s logs

run_case() {
  local case_name="$1"
  local values_file="$2"
  local time_scale="$3"
  local out_dir="artifacts/m6/${case_name}"
  local case_run_id="${RUN_ID}_${case_name}_ts${time_scale//./}"

  helm --kubeconfig "${KUBECONFIG}" upgrade --install "${RELEASE}" vllm/vllm-stack \
    --namespace "${NAMESPACE}" \
    --create-namespace \
    -f "${values_file}"

  sudo k3s kubectl rollout status deployment -n "${NAMESPACE}" -l "app.kubernetes.io/instance=${RELEASE}" --timeout=1200s
  sudo k3s kubectl get pods -n "${NAMESPACE}" -o wide | tee "artifacts/m6/k8s/pods_${case_name}_ts${time_scale//./}.txt"

  if [ -f logs/m6_port_forward.pid ]; then
    kill "$(cat logs/m6_port_forward.pid)" >/dev/null 2>&1 || true
  fi
  nohup sudo k3s kubectl port-forward -n "${NAMESPACE}" "svc/${SERVICE}" "${LOCAL_PORT}:80" \
    > "logs/m6_port_forward_${case_name}.log" 2>&1 &
  echo "$!" > logs/m6_port_forward.pid

  for _ in $(seq 1 90); do
    if curl -fsS "http://127.0.0.1:${LOCAL_PORT}/v1/models" >/dev/null 2>&1; then
      break
    fi
    sleep 5
  done
  curl -fsS "http://127.0.0.1:${LOCAL_PORT}/v1/models" | tee "artifacts/m6/k8s/models_${case_name}_ts${time_scale//./}.json"

  python replay/replay_trace_pack.py \
    --manifest "${TRACE_MANIFEST}" \
    --base-url "http://127.0.0.1:${LOCAL_PORT}" \
    --model "${MODEL}" \
    --out "${out_dir}" \
    --run-id "${case_run_id}" \
    --time-scale "${time_scale}"
}

helm repo add vllm https://vllm-project.github.io/production-stack
helm repo update

case_enabled() {
  case ",${M6_CASES}," in
    *",$1,"*) return 0 ;;
    *) return 1 ;;
  esac
}

if case_enabled "baseline"; then
  run_case "baseline" "deploy/k3s-vllm-stack/values-qwen-0.5b.yaml" "1.0"
fi
if case_enabled "baseline-pressure"; then
  run_case "baseline-pressure" "deploy/k3s-vllm-stack/values-qwen-0.5b.yaml" "0.25"
fi
if case_enabled "scaling"; then
  run_case "scaling" "deploy/k3s-vllm-stack/values-qwen-0.5b-2replica.yaml" "1.0"
fi
if case_enabled "scaling-pressure"; then
  run_case "scaling-pressure" "deploy/k3s-vllm-stack/values-qwen-0.5b-2replica.yaml" "0.25"
fi

if [ -f logs/m6_port_forward.pid ]; then
  kill "$(cat logs/m6_port_forward.pid)" >/dev/null 2>&1 || true
  rm -f logs/m6_port_forward.pid
fi

cat > "artifacts/m6/metadata_${RUN_ID}.json" <<EOF
{
  "milestone": "m6",
  "run_id": "${RUN_ID}",
  "model": "${MODEL}",
  "trace_manifest": "${TRACE_MANIFEST}",
  "cases": "${M6_CASES}"
}
EOF

echo "Milestone 6 scaling matrix complete: ${RUN_ID}"
