from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.integrations.errors import ModelGatewayError


class ModelGatewayClient:
    def __init__(self, timeout_seconds: float = 60.0) -> None:
        settings = get_settings()
        self.base_url = settings.model_base_url
        self.api_key = settings.model_api_key
        self.chat_model = settings.chat_model
        self.embedding_model = settings.embedding_model
        self.rerank_model = settings.rerank_model
        self.timeout = httpx.Timeout(timeout_seconds)

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        payload = {
            "model": kwargs.pop("model", self.chat_model),
            "messages": messages,
            **kwargs,
        }
        return await self._post("/chat/completions", payload)

    async def embed(self, text: str | list[str]) -> list[list[float]]:
        payload = {
            "model": self.embedding_model,
            "input": text,
        }
        response = await self._post("/embeddings", payload)
        return [item["embedding"] for item in response.get("data", [])]

    async def rerank(self, query: str, documents: list[str], top_n: int = 10) -> dict[str, Any]:
        payload = {
            "model": self.rerank_model,
            "query": query,
            "documents": documents,
            "top_n": top_n,
        }
        return await self._post("/rerank", payload)

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post(path, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            raise ModelGatewayError(f"Model gateway request failed: {exc}") from exc
