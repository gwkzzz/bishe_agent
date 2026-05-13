from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.integrations.errors import AlgorithmClientError


class AlgorithmClient:
    def __init__(
        self,
        base_url: str | None = None,
        internal_token: str | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        settings = get_settings()
        self.base_url = base_url or settings.algorithm_base_url
        self.internal_token = internal_token or settings.algorithm_internal_token
        self.timeout = httpx.Timeout(timeout_seconds)

    async def post_json(
        self,
        path: str,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        headers = {
            "X-Internal-Token": self.internal_token,
            get_settings().trace_header_name: trace_id,
        }
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post(path, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            raise AlgorithmClientError(f"Algorithm request failed: {exc}") from exc

    async def analyze_case(self, payload: dict[str, Any], trace_id: str) -> dict[str, Any]:
        return await self.post_json("/internal/agent/analyze", payload, trace_id)

    async def generate_arbitration_document(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        return await self.post_json("/internal/documents/arbitration", payload, trace_id)

    async def analyze_evidence(self, payload: dict[str, Any], trace_id: str) -> dict[str, Any]:
        return await self.post_json("/internal/evidence/analyze", payload, trace_id)
