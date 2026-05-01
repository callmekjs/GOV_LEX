#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${1:-configs/pipeline.yaml}"

echo "[run] pipeline config=${CONFIG_PATH}"
python -m govlexops.etl.pipeline --config "${CONFIG_PATH}"

echo "[run] refresh dashboard"
python scripts/build_dashboard.py

echo "[done] pipeline and dashboard complete"
