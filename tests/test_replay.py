from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from govlexops.core import replay
from govlexops.schemas.legal_document import LegalDocument, make_content_hash


def _doc(source_id: str, title: str) -> dict:
    return LegalDocument(
        source_id=source_id,
        jurisdiction="KR",
        source_type="law",
        language="ko",
        title=title,
        issued_date=date(2025, 1, 1),
        source_url=f"https://example.com/{source_id}",
        content_hash=make_content_hash(f"{title}_20250101"),
        metadata={},
    ).model_dump(mode="json")


def test_replay_run_writes_report(tmp_path: Path, monkeypatch):
    run_dir = tmp_path / "runs" / "run_test_1"
    run_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(replay, "load_documents", lambda: [_doc("a", "A법"), _doc("b", "B법")])

    out = replay.replay_run(str(run_dir))
    content = out.read_text(encoding="utf-8")

    assert out.exists()
    assert "Replay Report" in content
    assert "replay 입력 문서" in content


def test_replay_only_failures_filters_sources(tmp_path: Path, monkeypatch):
    run_dir = tmp_path / "runs" / "run_test_2"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "quality_failures.jsonl").write_text(
        json.dumps({"source_id": "keep_me"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    docs = [_doc("keep_me", "유지법"), _doc("drop_me", "제외법")]
    monkeypatch.setattr(replay, "load_documents", lambda: docs)

    out = replay.replay_run(str(run_dir), only_failures=True)
    text = out.read_text(encoding="utf-8")
    assert "replay 입력 문서: `1`" in text


def test_replay_regenerate_report_creates_quality_report(tmp_path: Path, monkeypatch):
    run_dir = tmp_path / "runs" / "run_test_3"
    run_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(replay, "load_documents", lambda: [_doc("a", "A법")])

    replay.replay_run(str(run_dir), regenerate_report=True)
    replay_quality = run_dir / "replay_latest" / "quality_report.md"
    assert replay_quality.exists()
