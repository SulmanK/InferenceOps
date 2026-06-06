#!/usr/bin/env bash
set -euo pipefail

URL="${1:?usage: m2_wait_for_endpoint.sh URL [SECONDS]}"
SECONDS_TO_WAIT="${2:-600}"

deadline=$((SECONDS + SECONDS_TO_WAIT))
while [ "${SECONDS}" -lt "${deadline}" ]; do
  if curl -fsS "${URL}" >/dev/null 2>&1; then
    echo "ready: ${URL}"
    exit 0
  fi
  sleep 5
done

echo "timed out waiting for ${URL}"
exit 1

