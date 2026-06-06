#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-0.5B-Instruct}"
POLICIES="${POLICIES:-round_robin,cache_aware,power_of_two}"
TRACE_MANIFEST="${TRACE_MANIFEST:-traces/pack_v1/manifest.json}"
OUT_DIR="${OUT_DIR:-artifacts/m2/replay}"
GATEWAY_PORT="${GATEWAY_PORT:-30000}"
WORKER1_PORT="${WORKER1_PORT:-31001}"
WORKER2_PORT="${WORKER2_PORT:-31002}"
TIME_SCALE="${TIME_SCALE:-1.0}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

mkdir -p "${OUT_DIR}" artifacts/m2 logs

bash deploy/sglang/m2_wait_for_endpoint.sh "http://127.0.0.1:${WORKER1_PORT}/v1/models" 900
bash deploy/sglang/m2_wait_for_endpoint.sh "http://127.0.0.1:${WORKER2_PORT}/v1/models" 900

IFS=',' read -r -a policy_list <<< "${POLICIES}"
for policy in "${policy_list[@]}"; do
  policy="$(echo "${policy}" | xargs)"
  [ -n "${policy}" ] || continue

  bash deploy/sglang/m2_stop_gateway.sh || true
  POLICY="${policy}" bash deploy/sglang/m2_start_gateway.sh
  bash deploy/sglang/m2_wait_for_endpoint.sh "http://127.0.0.1:${GATEWAY_PORT}/v1/models" 300

  python replay/replay_trace_pack.py \
    --manifest "${TRACE_MANIFEST}" \
    --base-url "http://127.0.0.1:${GATEWAY_PORT}" \
    --model "${MODEL}" \
    --out "${OUT_DIR}" \
    --run-id "${RUN_ID}_${policy}" \
    --time-scale "${TIME_SCALE}"

  cp "logs/sglang_gateway_${policy}.log" "${OUT_DIR}/sglang_gateway_${RUN_ID}_${policy}.log" || true
done

bash deploy/sglang/m2_stop_gateway.sh || true

cat > "artifacts/m2/metadata_${RUN_ID}.json" <<EOF
{
  "milestone": "m2",
  "run_id": "${RUN_ID}",
  "model": "${MODEL}",
  "trace_manifest": "${TRACE_MANIFEST}",
  "policies": "${POLICIES}",
  "gateway_port": ${GATEWAY_PORT},
  "worker_ports": [${WORKER1_PORT}, ${WORKER2_PORT}],
  "time_scale": ${TIME_SCALE}
}
EOF

echo "Milestone 2 policy matrix complete: ${RUN_ID}"

