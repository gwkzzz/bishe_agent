from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

import structlog

from app.core.config import get_settings
from app.integrations.errors import VectorStoreError
from app.integrations.milvus_client import MilvusClient
from app.retrieval.bm25 import BM25Index, build_seed_bm25_index
from app.retrieval.corpus import CollectionName
from app.retrieval.tokenizer import keyword_overlap_score, stable_embedding
from app.retrieval.types import RetrievalResult


logger = structlog.get_logger(__name__)

_VECTOR_COLLECTIONS: dict[CollectionName, str] = {
    "labor_law": "labor_law_chunks",
    "labor_precedent": "labor_precedent_chunks",
    "labor_template": "labor_template_chunks",
    "labor_limitation_rule": "labor_law_chunks",
}


class HybridSearchService:
    def __init__(
        self,
        *,
        law_index: BM25Index | None = None,
        precedent_index: BM25Index | None = None,
        template_index: BM25Index | None = None,
        limitation_rule_index: BM25Index | None = None,
        milvus: MilvusClient | None = None,
    ) -> None:
        self.settings = get_settings()
        self._indices: dict[CollectionName, BM25Index] = {
            "labor_law": law_index or build_seed_bm25_index("labor_law"),
            "labor_precedent": precedent_index or build_seed_bm25_index("labor_precedent"),
            "labor_template": template_index or build_seed_bm25_index("labor_template"),
            "labor_limitation_rule": limitation_rule_index
            or build_seed_bm25_index("labor_limitation_rule"),
        }
        self.milvus = milvus or MilvusClient()

    def search_laws(
        self,
        query: str,
        *,
        top_k: int = 5,
        trace_id: str | None = None,
        case_id: str | None = None,
    ) -> list[RetrievalResult]:
        rewritten = query_rewrite(query)
        candidates = [
            *self._search_collection("labor_law", rewritten, top_k=top_k * 3),
            *self._search_collection("labor_limitation_rule", rewritten, top_k=top_k),
        ]
        return self._merge_rerank_filter(
            query=rewritten,
            candidates=candidates,
            top_k=top_k,
            trace_id=trace_id,
            case_id=case_id,
            require_effective=True,
        )

    def search_precedents(
        self,
        query: str,
        *,
        top_k: int = 5,
        trace_id: str | None = None,
        case_id: str | None = None,
    ) -> list[RetrievalResult]:
        rewritten = query_rewrite(query)
        candidates = self._search_collection("labor_precedent", rewritten, top_k=top_k * 4)
        return self._merge_rerank_filter(
            query=rewritten,
            candidates=candidates,
            top_k=top_k,
            trace_id=trace_id,
            case_id=case_id,
            require_effective=False,
        )

    def search_templates(
        self,
        query: str,
        *,
        top_k: int = 5,
        trace_id: str | None = None,
        case_id: str | None = None,
    ) -> list[RetrievalResult]:
        rewritten = query_rewrite(query)
        candidates = self._search_collection("labor_template", rewritten, top_k=top_k * 3)
        return self._merge_rerank_filter(
            query=rewritten,
            candidates=candidates,
            top_k=top_k,
            trace_id=trace_id,
            case_id=case_id,
            require_effective=False,
        )

    def _search_collection(
        self,
        collection: CollectionName,
        query: str,
        *,
        top_k: int,
    ) -> list[RetrievalResult]:
        bm25_results = self._indices[collection].search(
            query,
            top_k=top_k,
            min_score=self.settings.rag_min_relevance_score,
        )
        vector_results = self._search_vector(collection, query, top_k=top_k)
        return [*bm25_results, *vector_results]

    def _search_vector(
        self,
        collection: CollectionName,
        query: str,
        *,
        top_k: int,
    ) -> list[RetrievalResult]:
        if not self.settings.rag_vector_enabled:
            return []

        vector = stable_embedding(query, dimension=self.settings.rag_vector_dimension)
        if not any(vector):
            return []

        collection_name = _VECTOR_COLLECTIONS[collection]
        try:
            hits = self.milvus.search(
                collection_name,
                vector,
                limit=top_k,
                output_fields=["source_id", "title", "text", "source_url", "article", "metadata_json"],
            )
        except VectorStoreError as exc:
            logger.warning(
                "rag_vector_search_degraded",
                collection=collection_name,
                error=str(exc),
            )
            return []

        results: list[RetrievalResult] = []
        for hit in hits:
            entity = hit.get("entity", {})
            metadata = _safe_json_dict(entity.get("metadata_json"))
            metadata["retrieval_channels"] = ["vector"]
            metadata["vector_collection"] = collection_name
            results.append(
                RetrievalResult(
                    source_id=str(entity.get("source_id") or hit.get("id")),
                    title=str(entity.get("title") or ""),
                    article=entity.get("article"),
                    text=str(entity.get("text") or ""),
                    score=float(hit.get("score") or 0.0),
                    source_url=entity.get("source_url") or None,
                    collection=collection,
                    metadata=metadata,
                )
            )
        return results

    def _merge_rerank_filter(
        self,
        *,
        query: str,
        candidates: list[RetrievalResult],
        top_k: int,
        trace_id: str | None,
        case_id: str | None,
        require_effective: bool,
    ) -> list[RetrievalResult]:
        deduped = _merge_by_source_id(candidates)
        verified = [
            item
            for item in deduped
            if self._passes_source_filter(
                item,
                require_effective=require_effective,
                trace_id=trace_id,
                case_id=case_id,
            )
        ]
        reranked = sorted(
            (self._rerank_result(query, item) for item in verified),
            key=lambda item: item.score,
            reverse=True,
        )
        return reranked[:top_k]

    def _passes_source_filter(
        self,
        item: RetrievalResult,
        *,
        require_effective: bool,
        trace_id: str | None,
        case_id: str | None,
    ) -> bool:
        metadata = item.metadata or {}
        if not item.source_id and not item.source_url:
            logger.info(
                "rag_source_filtered",
                reason="missing_source",
                trace_id=trace_id,
                case_id=case_id,
                title=item.title,
            )
            return False
        if require_effective and metadata.get("status") not in (None, "effective", "active"):
            logger.info(
                "rag_source_filtered",
                reason="inactive_source",
                trace_id=trace_id,
                case_id=case_id,
                source_id=item.source_id,
            )
            return False
        return True

    def _rerank_result(self, query: str, item: RetrievalResult) -> RetrievalResult:
        overlap = keyword_overlap_score(query, f"{item.title}\n{item.article or ''}\n{item.text}")
        channels = (item.metadata or {}).get("retrieval_channels", [])
        channel_bonus = 0.04 if "bm25" in channels and "vector" in channels else 0.0
        source_bonus = 0.03 if item.source_url else 0.01
        score = min(1.0, item.score * 0.72 + overlap * 0.25 + channel_bonus + source_bonus)
        metadata = {
            **(item.metadata or {}),
            "source_verified": bool(item.source_id or item.source_url),
            "rerank": "local_overlap",
        }
        return RetrievalResult(
            source_id=item.source_id,
            title=item.title,
            article=item.article,
            text=item.text,
            score=round(score, 4),
            source_url=item.source_url,
            collection=item.collection,
            metadata=metadata,
        )


def query_rewrite(query: str) -> str:
    normalized = " ".join(query.split())
    expansions = []
    if any(keyword in normalized for keyword in ("欠薪", "拖欠工资", "工资")):
        expansions.extend(["劳动报酬", "工资流水", "仲裁时效"])
    if any(keyword in normalized for keyword in ("未签", "没签", "合同")):
        expansions.extend(["未订立书面劳动合同", "二倍工资", "劳动关系"])
    if any(keyword in normalized for keyword in ("辞退", "开除", "解除", "赔偿")):
        expansions.extend(["违法解除", "赔偿金", "解除通知"])
    if "加班" in normalized:
        expansions.extend(["加班费", "考勤记录", "延长工作时间"])
    if "离职证明" in normalized:
        expansions.extend(["离职证明", "用人单位义务"])
    suffix = " ".join(item for item in expansions if item not in normalized)
    return f"{normalized} {suffix}".strip()


@lru_cache
def get_hybrid_search_service() -> HybridSearchService:
    return HybridSearchService()


def _merge_by_source_id(candidates: list[RetrievalResult]) -> list[RetrievalResult]:
    merged: dict[str, RetrievalResult] = {}
    for item in candidates:
        key = item.source_id or f"{item.title}:{item.source_url or ''}"
        if not key:
            continue

        existing = merged.get(key)
        if existing is None:
            merged[key] = item
            continue

        channels = set((existing.metadata or {}).get("retrieval_channels", []))
        channels.update((item.metadata or {}).get("retrieval_channels", []))
        metadata: dict[str, Any] = {
            **(existing.metadata or {}),
            **(item.metadata or {}),
            "retrieval_channels": sorted(channels),
        }
        better = item if item.score > existing.score else existing
        merged[key] = RetrievalResult(
            source_id=better.source_id,
            title=better.title or existing.title,
            article=better.article or existing.article,
            text=better.text or existing.text,
            score=max(existing.score, item.score),
            source_url=better.source_url or existing.source_url,
            collection=better.collection or existing.collection,
            metadata=metadata,
        )
    return list(merged.values())


def _safe_json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        payload = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}
