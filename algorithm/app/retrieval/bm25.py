from __future__ import annotations

from dataclasses import replace

from rank_bm25 import BM25Okapi

from app.retrieval.corpus import CollectionName, KnowledgeDocument, load_seed_documents
from app.retrieval.tokenizer import keyword_overlap_score, tokenize
from app.retrieval.types import RetrievalResult


class BM25Index:
    def __init__(self, name: str, documents: list[KnowledgeDocument]) -> None:
        self.name = name
        self.documents = _dedupe_documents(documents)
        self._tokenized = [tokenize(document.search_text) for document in self.documents]
        self._index = BM25Okapi(self._tokenized) if self._tokenized else None

    def search(self, query: str, top_k: int = 10, min_score: float = 0.02) -> list[RetrievalResult]:
        if not self._index or not query.strip():
            return []

        query_tokens = tokenize(query)
        raw_scores = self._index.get_scores(query_tokens)
        scored: list[tuple[float, KnowledgeDocument]] = []
        for document, raw_score in zip(self.documents, raw_scores, strict=False):
            overlap = keyword_overlap_score(query, document.search_text)
            score = _normalize_score(float(raw_score), overlap)
            if score >= min_score:
                scored.append((score, document))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            RetrievalResult(
                source_id=document.source_id,
                title=document.title,
                article=document.article,
                text=document.text,
                score=score,
                source_url=document.source_url,
                collection=document.collection,
                metadata={
                    **(document.metadata or {}),
                    "bm25_index": self.name,
                    "retrieval_channels": ["bm25"],
                    "status": document.status,
                },
            )
            for score, document in scored[:top_k]
        ]


def build_seed_bm25_index(collection: CollectionName) -> BM25Index:
    index_name = {
        "labor_law": "labor_law_bm25",
        "labor_precedent": "labor_precedent_bm25",
        "labor_template": "labor_template_bm25",
        "labor_limitation_rule": "labor_limitation_rule_bm25",
    }[collection]
    return BM25Index(index_name, load_seed_documents(collection))


def _dedupe_documents(documents: list[KnowledgeDocument]) -> list[KnowledgeDocument]:
    seen: set[str] = set()
    deduped: list[KnowledgeDocument] = []
    for document in documents:
        key = document.source_id.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(replace(document, source_id=key))
    return deduped


def _normalize_score(raw_score: float, overlap: float) -> float:
    bm25_component = raw_score / (raw_score + 3.0) if raw_score > 0 else 0.0
    return min(1.0, (bm25_component * 0.72) + (overlap * 0.28))
