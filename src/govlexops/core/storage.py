"""
정제된 문서를 data_index/normalized/docs.jsonl에 저장하는 모듈.
"""
import json
from pathlib import Path
from govlexops.schemas.legal_document import LegalDocument


DOCS_PATH = Path("data_index/normalized/docs.jsonl")


def save_documents(docs: list[LegalDocument]) -> int:
    """
    LegalDocument 목록을 docs.jsonl에 추가 저장합니다.
    반환값: 저장된 건수
    """
    DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with open(DOCS_PATH, "a", encoding="utf-8") as f:
        for doc in docs:
            f.write(
                json.dumps(doc.model_dump(mode="json"), ensure_ascii=False) + "\n"
            )
            count += 1
    return count


def load_documents() -> list[dict]:
    """docs.jsonl에서 전체 문서를 읽어옵니다."""
    if not DOCS_PATH.exists():
        return []
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def count_documents() -> dict:
    """국가별 문서 수를 셉니다."""
    docs = load_documents()
    result = {"KR": 0, "US": 0, "total": 0}
    for doc in docs:
        jurisdiction = doc.get("jurisdiction", "")
        if jurisdiction in result:
            result[jurisdiction] += 1
        result["total"] += 1
    return result