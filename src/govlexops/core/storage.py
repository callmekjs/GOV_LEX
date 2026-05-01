"""
정제된 문서를 data_index/normalized/docs.jsonl에 저장하는 모듈.
"""

import json
from pathlib import Path

from govlexops.core.atomic import atomic_append_jsonl
from govlexops.schemas.legal_document import LegalDocument

DOCS_PATH = Path("data_index/normalized/docs.jsonl")


def save_documents(docs: list[LegalDocument]) -> int:
    """
    LegalDocument 목록을 docs.jsonl에 추가 저장합니다.

    [pipline_upgrade 0-6]
    원자적 쓰기:
      이전엔 open(path, "a")로 직접 append했다. 도중에 죽으면 반쪽 파일.
      이제 staging → atomic rename 패턴으로 교체. 도중에 죽어도 docs.jsonl은
      이전 상태 그대로 유지된다.

    반환값:
      실제로 저장된 건수. (입력 docs 길이와 같음)
    """
    if not docs:
        return 0

    DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        json.dumps(doc.model_dump(mode="json"), ensure_ascii=False) for doc in docs
    ]
    return atomic_append_jsonl(DOCS_PATH, lines)


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
