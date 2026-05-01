#!/usr/bin/env bash
set -euo pipefail

echo "[smoke] lint/type/tests"
ruff check src/
mypy src/govlexops --ignore-missing-imports
pytest tests/test_config.py tests/test_metrics_dashboard.py -q

echo "[smoke] run pipeline (dev config)"
python -m govlexops.etl.pipeline --config configs/dev.yaml
python scripts/build_dashboard.py

echo "[done] smoke test complete"
