#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: scripts/replay_run.sh <run_path> [--only-failures] [--regenerate-report]"
  exit 1
fi

RUN_PATH="$1"
shift || true

python -m govlexops.services.cli replay --run-path "${RUN_PATH}" "$@"
