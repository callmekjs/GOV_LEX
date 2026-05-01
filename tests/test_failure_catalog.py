from __future__ import annotations

import json
import importlib.util
from pathlib import Path

from govlexops.qa import failure_catalog


def _load_analyze_failures_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "analyze_failures.py"
    spec = importlib.util.spec_from_file_location("analyze_failures", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_append_to_catalog_writes_record(tmp_path: Path, monkeypatch):
    cat_path = tmp_path / "failure_catalog.jsonl"
    monkeypatch.setattr(failure_catalog, "CATALOG_PATH", cat_path)

    failure_catalog.append_to_catalog(
        {
            "failure_id": "F0001",
            "rule_id": "R02",
            "source_id": "kr_assembly_123",
            "observed": "결측 필드: title",
        }
    )

    assert cat_path.exists()
    row = json.loads(cat_path.read_text(encoding="utf-8").splitlines()[0])
    assert row["rule_id"] == "R02"
    assert row["source_type"] == "bill"
    assert row["jurisdiction"] == "KR"


def test_build_failure_patterns_from_catalog(tmp_path: Path, monkeypatch):
    analyze_failures = _load_analyze_failures_module()
    catalog_path = tmp_path / "failure_catalog.jsonl"
    out_path = tmp_path / "failure_patterns.md"
    catalog_path.write_text(
        "\n".join(
            [
                json.dumps({"rule_id": "R01", "source_type": "law", "jurisdiction": "KR"}),
                json.dumps({"rule_id": "R01", "source_type": "law", "jurisdiction": "KR"}),
                json.dumps(
                    {"rule_id": "R02", "source_type": "bill", "jurisdiction": "US"}
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(analyze_failures, "CATALOG_PATH", catalog_path)
    monkeypatch.setattr(analyze_failures, "OUTPUT_PATH", out_path)

    out = analyze_failures.build_failure_patterns()
    content = out.read_text(encoding="utf-8")
    assert out.exists()
    assert "| R01 | 2 |" in content
    assert "| law | 2 |" in content
