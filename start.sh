#!/bin/sh
set -e

if [ -z "${MARKER_API_KEY}" ] && [ "${MARKER_ALLOW_NO_API_KEY}" != "true" ]; then
  echo "MARKER_API_KEY is empty. Set it (the Railway template generates one) or set MARKER_ALLOW_NO_API_KEY=true to run without authentication." >&2
  exit 1
fi

# PyTorch and ONNX Runtime start one thread per host core, which oversubscribes
# a container's CPU quota. Size the thread pools from the cgroup limit (max 8).
if [ -z "${OMP_NUM_THREADS}" ]; then
  threads=4
  if [ -r /sys/fs/cgroup/cpu.max ]; then
    read -r quota period < /sys/fs/cgroup/cpu.max || true
    if [ "${quota}" != "max" ] && [ -n "${period}" ] && [ "${period}" -gt 0 ] 2>/dev/null; then
      threads=$(( (quota + period - 1) / period ))
    else
      threads=$(nproc)
    fi
  else
    threads=$(nproc)
  fi
  [ "${threads}" -gt 8 ] && threads=8
  [ "${threads}" -lt 1 ] && threads=1
  export OMP_NUM_THREADS="${threads}"
fi
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-$OMP_NUM_THREADS}"

exec python /app/app.py
