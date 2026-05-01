"""Analyze failure catalog and emit docs/failure_patterns.md."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


CATALOG_PATH = Path("data_index/quality/failure_catalog.jsonl")
OUTPUT_PATH = Path("docs/failure_patterns.md")


def _read_catalog() -> list[dict]:
    if not CATALOG_PATH.exists():
        return []
    rows: list[dict] = []
    for line in CATALOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def build_failure_patterns() -> Path:
    rows = _read_catalog()
    by_rule = Counter(r.get("rule_id", "UNKNOWN") for r in rows)
    by_source_type = Counter(r.get("source_type", "unknown") for r in rows)
    by_jurisdiction = Counter(r.get("jurisdiction", "UNKNOWN") for r in rows)

    lines: list[str] = [
        "# Failure Patterns",
        "",
        f"- total catalog records: `{len(rows)}`",
        "",
        "## Rule Frequency",
        "",
        "| rule_id | count |",
        "|---|---:|",
    ]
    for rule_id, count in by_rule.most_common():
        lines.append(f"| {rule_id} | {count} |")

    lines.extend(
        [
            "",
            "## Source Type Frequency",
            "",
            "| source_type | count |",
            "|---|---:|",
        ]
    )
    for source_type, count in by_source_type.most_common():
        lines.append(f"| {source_type} | {count} |")

    lines.extend(
        [
            "",
            "## Jurisdiction Frequency",
            "",
            "| jurisdiction | count |",
            "|---|---:|",
        ]
    )
    for jurisdiction, count in by_jurisdiction.most_common():
        lines.append(f"| {jurisdiction} | {count} |")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This report is generated from `data_index/quality/failure_catalog.jsonl`.",
            "- It is a catalog for pattern tracking, not a learning/reflexion system.",
        ]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return OUTPUT_PATH


if __name__ == "__main__":
    out = build_failure_patterns()
    print(f"failure patterns generated: {out}")
