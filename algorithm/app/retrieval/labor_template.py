from __future__ import annotations

from app.integrations.milvus_client import MilvusClient
from app.retrieval.hybrid import HybridSearchService
from app.retrieval.types import RetrievalResult


class LaborTemplateRetriever:
    def __init__(self, milvus: MilvusClient | None = None) -> None:
        self.milvus = milvus or MilvusClient()

    def search(self, query: str, limit: int = 10) -> list[RetrievalResult]:
        return HybridSearchService(milvus=self.milvus).search_templates(query, top_k=limit)
