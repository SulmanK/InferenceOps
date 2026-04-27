#!/usr/bin/env bash
set -euo pipefail

echo "InferenceOps Milestone 0 WSL/vLLM preflight"
echo

if ! grep -qi microsoft /proc/version 2>/dev/null; then
  echo "WSL: not detected"
else
  echo "WSL: detected"
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3: missing"
else
  echo "python3: $(python3 --version)"
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi: missing"
  echo "Result: GPU is not visible inside this Linux environment."
  exit 1
fi

echo
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader || {
  echo "nvidia-smi is present, but compute capability query failed."
  nvidia-smi
  exit 1
}

compute_cap="$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -n 1 | tr -d '[:space:]')"
major="${compute_cap%%.*}"
minor="${compute_cap#*.}"

echo
echo "Detected compute capability: ${compute_cap}"

if [ "${major}" -gt 7 ] || { [ "${major}" -eq 7 ] && [ "${minor}" -ge 5 ]; }; then
  echo "Result: GPU meets current vLLM NVIDIA requirement for prebuilt wheels."
  exit 0
fi

echo "Result: GPU does not meet current vLLM NVIDIA requirement for prebuilt wheels."
echo "Milestone 0 vLLM should run on a cloud GPU such as T4, L4, A10, A100, or a local RTX 20xx+ GPU."
exit 2

