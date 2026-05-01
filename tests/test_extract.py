from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from govlexops.etl.extract import (
    build_entity_relation_records,
    extract_entities_relations_from_assembly_bill,
    write_extracted_graph,
)
from govlexops.schemas.legal_document import LegalDocument, make_content_hash


def _assembly_doc(
    source_id: str,
    proposer: str,
    committee: str,
    title: str = "테스트 법안",
) -> LegalDocument:
    return LegalDocument(
        source_id=source_id,
        jurisdiction="KR",
        source_type="bill",
        language="ko",
        title=title,
        issued_date=date(2024, 6, 1),
        source_url="https://open.assembly.go.kr/mock",
        content_hash=make_content_hash(f"{title}_20240601_{source_id}"),
        metadata={"ppsr_nm": proposer, "jrcmit_nm": committee},
    )


def test_extract_entities_relations_from_assembly_bill():
    doc = _assembly_doc("kr_assembly_B001", "홍길동", "과방위")
    entities, relations = extract_entities_relations_from_assembly_bill(doc)

    assert len(entities) == 2
    assert len(relations) == 2
    assert any(e["type"] == "Member" and e["name"] == "홍길동" for e in entities)
    assert any(r["type"] == "PROPOSED_BY" for r in relations)


def test_build_entity_relation_records_dedupes_entities():
    d1 = _assembly_doc("kr_assembly_B001", "홍길동", "과방위", title="법안1")
    d2 = _assembly_doc("kr_assembly_B002", "홍길동", "과방위", title="법안2")

    entities, relations = build_entity_relation_records([d1, d2])
    # 같은 인물/위원회는 엔티티 1건으로 dedupe
    assert len(entities) == 2
    # 관계는 문서별로 남아야 함
    assert len(relations) == 4


def test_write_extracted_graph_writes_jsonl(tmp_path: Path):
    docs = [
        _assembly_doc("kr_assembly_B001", "홍길동", "과방위"),
        _assembly_doc("kr_assembly_B002", "김철수", "법사위"),
    ]
    out_dir = tmp_path / "data_index" / "extracted"
    entities_written, relations_written = write_extracted_graph(docs, out_dir)

    assert entities_written == 4
    assert relations_written == 4

    entities_path = out_dir / "entities.jsonl"
    relations_path = out_dir / "relations.jsonl"
    assert entities_path.exists()
    assert relations_path.exists()

    entities = [
        json.loads(line) for line in entities_path.read_text(encoding="utf-8").splitlines()
    ]
    relations = [
        json.loads(line)
        for line in relations_path.read_text(encoding="utf-8").splitlines()
    ]
    assert any(e["entity_id"].startswith("member::") for e in entities)
    assert any(r["type"] == "REVIEWED_BY" for r in relations)
