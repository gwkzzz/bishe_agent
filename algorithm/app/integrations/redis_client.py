from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

from app.core.config import get_settings
from app.integrations.errors import CacheError


class RedisClient:
    def __init__(self, url: str | None = None) -> None:
        self.url = url or get_settings().redis_url
        self._client: Redis | None = None

    @property
    def client(self) -> Redis:
        if self._client is None:
            self._client = Redis.from_url(self.url, decode_responses=True)
        return self._client

    async def get_json(self, key: str) -> dict[str, Any] | None:
        try:
            value = await self.client.get(key)
            return json.loads(value) if value else None
        except Exception as exc:
            raise CacheError(f"Redis get failed for key {key}") from exc

    async def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int | None = None) -> None:
        try:
            await self.client.set(
                key,
                json.dumps(value, ensure_ascii=False, default=str),
                ex=ttl_seconds,
            )
        except Exception as exc:
            raise CacheError(f"Redis set failed for key {key}") from exc

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
