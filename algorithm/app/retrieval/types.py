from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievalResult:
    source_id: str
    title: str
    text: str
    score: float
    source_url: str | None = None
    article: str | None = None
    collection: str | None = None
    metadata: dict[str, Any] | None = None
