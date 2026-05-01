"""BM25 + 해시 벡터 기반 하이브리드 검색 엔진."""

import json
import math
from pathlib import Path

from rank_bm25 import BM25Okapi

DOCS_PATH = Path("data_index/normalized/docs.jsonl")
_VEC_DIM = 256
_SYNONYMS = {
    "ai": ["인공지능", "artificial intelligence"],
    "인공지능": ["ai", "artificial intelligence"],
    "privacy": ["개인정보", "data protection"],
    "개인정보": ["privacy", "data protection"],
}


def _expand_query(query: str) -> str:
    tokens = query.split()
    expanded = list(tokens)
    for token in tokens:
        for key, values in _SYNONYMS.items():
            if token.lower() == key.lower():
                expanded.extend(values)
    return " ".join(expanded)


def _doc_text(doc: dict) -> str:
    return (
        doc.get("title", "")
        + " "
        + json.dumps(doc.get("metadata", {}), ensure_ascii=False)
    )


def _to_hashed_vector(text: str, dim: int = _VEC_DIM) -> list[float]:
    vec = [0.0] * dim
    for token in text.lower().split():
        idx = hash(token) % dim
        vec[idx] += 1.0
    return vec


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _minmax(values: list[float]) -> list[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if math.isclose(low, high):
        return [0.0 for _ in values]
    return [(v - low) / (high - low) for v in values]


def load_docs() -> list[dict]:
    """docs.jsonl 전체 로드."""
    if not DOCS_PATH.exists():
        return []
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def search(
    query: str,
    top_k: int = 10,
    jurisdiction: str = "전체",
    mode: str = "hybrid",
) -> list[dict]:
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

    expanded_query = _expand_query(query)
    corpus_tokens = [_doc_text(d).lower().split() for d in docs]
    bm25 = BM25Okapi(corpus_tokens)
    bm25_scores = list(bm25.get_scores(expanded_query.lower().split()))

    if mode == "bm25":
        top_indices = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True,
        )[:top_k]
        return [docs[i] for i in top_indices]

    # 하이브리드: BM25 + 해시 벡터 코사인
    query_vec = _to_hashed_vector(expanded_query)
    vec_scores = [_cosine(_to_hashed_vector(_doc_text(d)), query_vec) for d in docs]

    bm25_norm = _minmax(bm25_scores)
    vec_norm = _minmax(vec_scores)

    combined = [(0.6 * bm25_norm[i]) + (0.4 * vec_norm[i]) for i in range(len(docs))]
    top_indices = sorted(range(len(combined)), key=lambda i: combined[i], reverse=True)[
        :top_k
    ]
    return [docs[i] for i in top_indices if combined[i] > 0]
