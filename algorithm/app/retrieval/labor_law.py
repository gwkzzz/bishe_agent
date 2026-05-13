from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.integrations.milvus_client import MilvusClient
from app.retrieval.hybrid import HybridSearchService
from app.retrieval.types import RetrievalResult


class LaborLawRetriever:
    def __init__(self, db: Session, milvus: MilvusClient | None = None) -> None:
        self.db = db
        self.milvus = milvus or MilvusClient()

    def search(self, query: str, limit: int = 10) -> list[RetrievalResult]:
        return HybridSearchService(milvus=self.milvus).search_laws(query, top_k=limit)

    def search_bm25(self, query: str, limit: int = 10) -> list[RetrievalResult]:
        rows = self.db.execute(
            text(
                """
                SELECT id, bm25_doc_id, title, article, content, status, source_url
                FROM legal_sources
                WHERE status = 'effective'
                  AND (title LIKE :query OR article LIKE :query OR content LIKE :query)
                LIMIT :limit
                """
            ),
            {"query": f"%{query}%", "limit": limit},
        ).mappings()
        return [
            RetrievalResult(
                source_id=row["bm25_doc_id"] or row["id"],
                title=f"{row['title']} {row['article'] or ''}".strip(),
                text=row["content"],
                score=1.0,
                source_url=row["source_url"],
                article=row["article"],
                collection="labor_law",
                metadata={
                    "retrieval_channels": ["bm25"],
                    "bm25_index": "legal_sources_sql",
                    "status": row["status"],
                },
            )
            for row in rows
            if row["source_url"] or row["bm25_doc_id"] or row["id"]
        ]

    def search_vector(self, vector: list[float], limit: int = 10) -> list[RetrievalResult]:
        hits = self.milvus.search("labor_law_chunks", vector, limit=limit)
        return [
            RetrievalResult(
                source_id=str(hit["entity"].get("source_id") or hit["id"]),
                title=str(hit["entity"].get("title") or ""),
                text=str(hit["entity"].get("text") or ""),
                score=float(hit["score"]),
                source_url=hit["entity"].get("source_url"),
                article=hit["entity"].get("article"),
                collection="labor_law",
                metadata={"retrieval_channels": ["vector"]},
            )
            for hit in hits
        ]
