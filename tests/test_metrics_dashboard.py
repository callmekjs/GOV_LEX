from __future__ import annotations

import json
import importlib.util
from datetime import datetime
from pathlib import Path

from govlexops.etl.pipeline import _write_metrics


def _load_build_dashboard_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build_dashboard.py"
    spec = importlib.util.spec_from_file_location("build_dashboard", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_write_metrics_creates_metrics_json(tmp_path: Path):
    run_dir = tmp_path / "runs" / "run_20260501_000000_abc123"
    run_dir.mkdir(parents=True, exist_ok=True)

    payload = _write_metrics(
        run_dir,
        started_at=datetime(2026, 5, 1, 18, 0, 0),
        started_monotonic=0.0,
        all_docs_count=10,
        passed_count=8,
        saved_count=8,
        committed_count=8,
        qa_summary={"R01": 1, "R02": 1, "R07": 0, "R05": 0},
        by_source={"kr_law": 4, "us_congress": 3, "kr_assembly": 3},
    )

    metrics_path = run_dir / "metrics.json"
    assert metrics_path.exists()
    loaded = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert loaded["run_id"] == run_dir.name
    assert loaded["ingested"] == 10
    assert loaded["passed"] == 8
    assert loaded["pass_rate"] == 0.8
    assert payload["by_source"]["kr_law"] == 4


def test_build_dashboard_from_metrics(tmp_path: Path, monkeypatch):
    build_dashboard = _load_build_dashboard_module()
    runs_dir = tmp_path / "runs"
    docs_dir = tmp_path / "docs"
    run_dir = runs_dir / "run_20260501_101010_aaaaaa"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "metrics.json").write_text(
        json.dumps(
            {
                "run_id": run_dir.name,
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "finished_at": datetime.now().isoformat(timespec="seconds"),
                "duration_seconds": 12.34,
                "ingested": 20,
                "passed": 18,
                "saved": 18,
                "committed_seen": 18,
                "rejected": {"R01": 1, "R02": 1, "R07": 0, "R05": 0},
                "by_source": {"kr_law": 7, "us_congress": 7, "kr_assembly": 6},
                "pass_rate": 0.9,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(build_dashboard, "RUNS_DIR", runs_dir)
    monkeypatch.setattr(build_dashboard, "OUTPUT_PATH", docs_dir / "dashboard.md")
    out = build_dashboard.build_dashboard()
    content = out.read_text(encoding="utf-8")

    assert out.exists()
    assert "GovLex 운영 대시보드" in content
    assert run_dir.name in content
    assert "90.00%" in content
