"""Phase 3-3: KR 국회 법안에서 entities/relations를 추출한다."""

from __future__ import annotations

import json
from pathlib import Path

from govlexops.core.atomic import atomic_append_jsonl
from govlexops.schemas.legal_document import LegalDocument


def _clean(value: object) -> str:
    return str(value).strip() if value is not None else ""


def extract_entities_relations_from_assembly_bill(
    doc: LegalDocument,
) -> tuple[list[dict], list[dict]]:
    """국회 법안 1건에서 엔티티/관계를 추출한다."""
    if doc.jurisdiction != "KR" or doc.source_type != "bill":
        return [], []
    if not doc.source_id.startswith("kr_assembly_"):
        return [], []

    md = doc.metadata
    proposer = _clean(md.get("ppsr_nm"))
    committee = _clean(md.get("jrcmit_nm"))

    entities: list[dict] = []
    relations: list[dict] = []

    if proposer:
        entities.append(
            {
                "entity_id": f"member::{proposer}",
                "type": "Member",
                "name": proposer,
                "jurisdiction": "KR",
                "source_id": doc.source_id,
            }
        )
        relations.append(
            {
                "from": doc.source_id,
                "to": f"member::{proposer}",
                "type": "PROPOSED_BY",
                "jurisdiction": "KR",
            }
        )

    if committee:
        entities.append(
            {
                "entity_id": f"committee::{committee}",
                "type": "Committee",
                "name": committee,
                "jurisdiction": "KR",
                "source_id": doc.source_id,
            }
        )
        relations.append(
            {
                "from": doc.source_id,
                "to": f"committee::{committee}",
                "type": "REVIEWED_BY",
                "jurisdiction": "KR",
            }
        )

    return entities, relations


def build_entity_relation_records(
    docs: list[LegalDocument],
) -> tuple[list[dict], list[dict]]:
    """문서 목록에서 중복 제거된 엔티티/관계 레코드를 만든다."""
    entities: list[dict] = []
    relations: list[dict] = []

    entity_seen: set[tuple[str, str, str]] = set()
    relation_seen: set[tuple[str, str, str]] = set()

    for doc in docs:
        doc_entities, doc_relations = extract_entities_relations_from_assembly_bill(doc)
        for e in doc_entities:
            key = (e["type"], e["name"], e["jurisdiction"])
            if key in entity_seen:
                continue
            entity_seen.add(key)
            entities.append(e)

        for r in doc_relations:
            key = (r["from"], r["to"], r["type"])
            if key in relation_seen:
                continue
            relation_seen.add(key)
            relations.append(r)

    return entities, relations


def write_extracted_graph(
    docs: list[LegalDocument],
    extracted_dir: Path = Path("data_index/extracted"),
) -> tuple[int, int]:
    """entities/relations JSONL 파일에 추출 결과를 append한다."""
    entities, relations = build_entity_relation_records(docs)
    entities_path = extracted_dir / "entities.jsonl"
    relations_path = extracted_dir / "relations.jsonl"

    entities_lines = [json.dumps(row, ensure_ascii=False) for row in entities]
    relations_lines = [json.dumps(row, ensure_ascii=False) for row in relations]

    entities_written = atomic_append_jsonl(entities_path, entities_lines)
    relations_written = atomic_append_jsonl(relations_path, relations_lines)
    return entities_written, relations_written
