from __future__ import annotations

import json
from pathlib import Path

from govlexops.core.atomic import atomic_append_jsonl
from govlexops.schemas.legal_document import LegalDocument


class JsonlDocumentStore:
    def __init__(self, docs_path: Path | str = "data_index/normalized/docs.jsonl"):
        self.docs_path = Path(docs_path)

    def append(self, docs: list[LegalDocument]) -> int:
        if not docs:
            return 0
        self.docs_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            json.dumps(doc.model_dump(mode="json"), ensure_ascii=False) for doc in docs
        ]
        return atomic_append_jsonl(self.docs_path, lines)

    def load_all(self) -> list[dict]:
        if not self.docs_path.exists():
            return []
        with open(self.docs_path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def query(self, **filters) -> list[dict]:
        docs = self.load_all()
        if not filters:
            return docs
        result = []
        for d in docs:
            if all(d.get(k) == v for k, v in filters.items()):
                result.append(d)
        return result

    def count(self) -> dict:
        docs = self.load_all()
        result = {"KR": 0, "US": 0, "total": 0}
        for doc in docs:
            jurisdiction = doc.get("jurisdiction", "")
            if jurisdiction in result:
                result[jurisdiction] += 1
            result["total"] += 1
        return result
