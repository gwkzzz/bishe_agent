from __future__ import annotations

from pydantic import BaseModel

from app.schemas.cases import GeneratedDocumentRead


class ArbitrationDocumentRequest(BaseModel):
    case_id: str


class ArbitrationDocumentResponse(GeneratedDocumentRead):
    pass
