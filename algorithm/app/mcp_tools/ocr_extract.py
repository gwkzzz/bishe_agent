from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OcrExtractTool:
    name: str = "ocr.extract"

    async def extract(self, file_id: str, trace_id: str, case_id: str) -> dict:
        return {
            "tool": self.name,
            "file_id": file_id,
            "trace_id": trace_id,
            "case_id": case_id,
            "status": "not_configured",
            "text": "",
            "blocks": [],
        }
