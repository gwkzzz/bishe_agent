from __future__ import annotations

from app.model_gateway import ModelGatewayClient
from app.retrieval.types import RetrievalResult


class RerankerClient:
    def __init__(self, model_gateway: ModelGatewayClient | None = None) -> None:
        self.model_gateway = model_gateway or ModelGatewayClient()

    async def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        top_n: int = 10,
    ) -> list[RetrievalResult]:
        if not candidates:
            return []

        response = await self.model_gateway.rerank(
            query=query,
            documents=[candidate.text for candidate in candidates],
            top_n=min(top_n, len(candidates)),
        )
        results = response.get("results", [])
        if not results:
            return candidates[:top_n]

        ranked: list[RetrievalResult] = []
        for item in results:
            index = int(item.get("index", 0))
            if 0 <= index < len(candidates):
                original = candidates[index]
                ranked.append(
                    RetrievalResult(
                        source_id=original.source_id,
                        title=original.title,
                        text=original.text,
                        score=float(item.get("relevance_score", original.score)),
                        source_url=original.source_url,
                        metadata=original.metadata,
                    )
                )
        return ranked[:top_n]
