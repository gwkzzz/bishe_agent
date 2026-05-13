from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.cases import EvidenceItemRead


class AnalyzeEvidenceResponse(BaseModel):
    task_id: str
    evidence_id: str
    status: str


class TaskRead(BaseModel):
    id: str
    case_id: str | None
    evidence_id: str | None
    task_type: str
    status: str
    progress: int
    result_json: dict[str, Any] | None
    error_message: str | None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvidenceUploadResponse(EvidenceItemRead):
    pass
