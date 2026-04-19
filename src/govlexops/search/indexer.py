"""
BM25 기반 키워드 검색 엔진.
docs.jsonl을 읽어서 키워드로 문서를 찾아줍니다.
"""
import json
from pathlib import Path
from rank_bm25 import BM25Okapi

DOCS_PATH = Path("data_index/normalized/docs.jsonl")


def load_docs() -> list[dict]:
    """docs.jsonl 전체 로드."""
    if not DOCS_PATH.exists():
        return []
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def search(query: str, top_k: int = 10, jurisdiction: str = "전체") -> list[dict]:
    """
    키워드로 문서를 검색합니다.

    - query: 검색어
    - top_k: 결과 최대 개수
    - jurisdiction: "전체" / "KR" / "US"
    """
    docs = load_docs()

    if not docs:
        return []

    # 국가 필터
    if jurisdiction != "전체":
        docs = [d for d in docs if d.get("jurisdiction") == jurisdiction]

    if not docs:
        return []

    # BM25 인덱스 생성
    corpus = [
        (d.get("title", "") + " " + json.dumps(
            d.get("metadata", {}), ensure_ascii=False)
        ).split()
        for d in docs
    ]
    bm25 = BM25Okapi(corpus)

    # 검색
    scores = bm25.get_scores(query.split())
    top_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            results.append(docs[idx])

    return results