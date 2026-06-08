#!/usr/bin/env bash
set -euo pipefail

echo "== host =="
hostname || true
cat /etc/os-release || true

echo "== gpu =="
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi is missing. Use a Lambda GPU image with NVIDIA drivers installed."
  exit 1
fi
nvidia-smi

echo "== tools =="
for tool in curl sudo; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    echo "missing required tool: ${tool}"
    exit 1
  fi
done

mkdir -p artifacts/m5 logs
echo "preflight ok"
