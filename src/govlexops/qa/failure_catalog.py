"""Failure catalog appender (no learning, just accumulation)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from govlexops.core.atomic import atomic_append_jsonl


CATALOG_PATH = Path("data_index/quality/failure_catalog.jsonl")


def _infer_source_type(source_id: str) -> str:
    if source_id.startswith("kr_law_"):
        return "law"
    if source_id.startswith("us_congress_"):
        return "bill"
    if source_id.startswith("kr_assembly_"):
        return "bill"
    return "unknown"


def _infer_jurisdiction(source_id: str) -> str:
    if source_id.startswith("us_"):
        return "US"
    if source_id.startswith("kr_"):
        return "KR"
    return "UNKNOWN"


def append_to_catalog(failure: dict) -> None:
    """실패 한 건을 카탈로그에 append한다."""
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    source_id = str(failure.get("source_id", "") or "")
    record = {
        "failure_id": str(failure.get("failure_id", "")),
        "rule_id": str(failure.get("rule_id", "")),
        "source_id": source_id,
        "source_type": _infer_source_type(source_id),
        "jurisdiction": _infer_jurisdiction(source_id),
        "observed_at": datetime.now().isoformat(),
        "context_brief": str(failure.get("observed", ""))[:200],
    }
    atomic_append_jsonl(CATALOG_PATH, [json.dumps(record, ensure_ascii=False)])
