from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class SourceVerifyTool:
    name: str = "source.verify"

    async def verify(
        self,
        trace_id: str,
        case_id: str,
        source_url: str | None = None,
        source_id: str | None = None,
    ) -> dict:
        status = "verified" if source_id or source_url else "missing_source"
        return {
            "tool": self.name,
            "trace_id": trace_id,
            "case_id": case_id,
            "source_url": source_url,
            "source_id": source_id,
            "status": status,
            "degraded": True,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
